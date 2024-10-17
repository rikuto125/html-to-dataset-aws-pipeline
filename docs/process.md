# HTML to Dataset Conversion: Complete Setup Guide

## 1. S3バケットの作成と設定

1. AWS Management Consoleにログインし、S3サービスに移動します。
2. 「バケットを作成」をクリックします。
3. バケット名を「hoge」とし、リージョンを選択します。
4. その他の設定はデフォルトのままで、バケットを作成します。
5. 作成したバケット内に以下のフォルダを作成します：
   - html/
   - json/
   - 機械学習/

### バケットポリシーの設定

1. 作成したバケットの「アクセス許可」タブに移動します。
2. 「バケットポリシー」セクションで、以下のポリシーを入力します：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowLambdaAccess",
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::hoge",
                "arn:aws:s3:::hoge/*"
            ]
        }
    ]
}
```

## 2. IAMロールの作成

1. IAMサービスに移動します。
2. 「ロール」を選択し、「ロールの作成」をクリックします。
3. 信頼されたエンティティタイプとして「AWS サービス」を選択し、ユースケースで「Lambda」を選択します。
4. 以下のポリシーをアタッチします：
   - AWSLambdaBasicExecutionRole
   - AmazonS3FullAccess (本番環境では必要最小限の権限に絞ることをお勧めします)
5. ロール名を「LambdaS3ProcessingRole」として、ロールを作成します。

## 3. Lambda関数の作成

### 3.1 HTML to JSON Lambda関数

1. Lambdaサービスに移動し、「関数の作成」をクリックします。
2. 関数名を「HTML2JSONLambda」とし、ランタイムに「Python 3.8」を選択します。
3. 実行ロールで、先ほど作成した「LambdaS3ProcessingRole」を選択します。
4. 関数を作成後、以下のコードをコピーして貼り付けます：

```python
import json
import boto3
import os
from bs4 import BeautifulSoup

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # S3イベントからバケット名とオブジェクトキーを取得
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    try:
        # S3からHTMLファイルを読み込む
        response = s3.get_object(Bucket=bucket, Key=key)
        html_content = response['Body'].read().decode('utf-8')
        
        # HTMLをパースしてJSONに変換
        soup = BeautifulSoup(html_content, 'html.parser')
        json_content = {
            'title': soup.title.string if soup.title else '',
            'headings': [h.text for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])],
            'paragraphs': [p.text for p in soup.find_all('p')],
            'links': [{'text': a.text, 'href': a.get('href')} for a in soup.find_all('a')]
        }
        
        # JSONファイルのキーを生成
        json_key = key.replace('html/', 'json/').replace('.html', '.json')
        
        # JSONをS3に保存
        s3.put_object(
            Bucket=bucket,
            Key=json_key,
            Body=json.dumps(json_content, ensure_ascii=False, indent=2),
            ContentType='application/json'
        )
        
        print(f"Successfully converted {key} to JSON and saved as {json_key}")
        
        # 次のLambda関数を呼び出す
        lambda_client = boto3.client('lambda')
        lambda_client.invoke(
            FunctionName='JSON2DatasetLambda',
            InvocationType='Event',
            Payload=json.dumps({'bucket': bucket, 'key': json_key})
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'HTML to JSON conversion successful',
                'source': key,
                'destination': json_key
            })
        }
    
    except Exception as e:
        print(f"Error processing {key}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error during HTML to JSON conversion',
                'error': str(e)
            })
        }
```

5. 「設定」タブで、タイムアウトを3分に設定します。
6. BeautifulSoupライブラリを含むレイヤーを追加します。

### 3.2 JSON to Dataset Lambda関数

1. 新しいLambda関数を作成し、名前を「JSON2DatasetLambda」とします。
2. ランタイムに「Python 3.8」を選択し、実行ロールに「LambdaS3ProcessingRole」を選択します。
3. 以下のコードをコピーして貼り付けます：

```python
import json
import boto3
import os
import csv
from io import StringIO

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # イベントからバケット名とオブジェクトキーを取得
    bucket = event['bucket']
    key = event['key']
    
    try:
        # S3からJSONファイルを読み込む
        response = s3.get_object(Bucket=bucket, Key=key)
        json_content = json.loads(response['Body'].read().decode('utf-8'))
        
        # JSONからデータセットを作成
        dataset = create_dataset(json_content)
        
        # データセットファイルのキーを生成
        dataset_key = key.replace('json/', '機械学習/').replace('.json', '_dataset.csv')
        
        # データセットをCSV形式でS3に保存
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)
        csv_writer.writerows(dataset)
        
        s3.put_object(
            Bucket=bucket,
            Key=dataset_key,
            Body=csv_buffer.getvalue(),
            ContentType='text/csv'
        )
        
        print(f"Successfully created dataset from {key} and saved as {dataset_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'JSON to dataset conversion successful',
                'source': key,
                'destination': dataset_key
            })
        }
    
    except Exception as e:
        print(f"Error processing {key}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error during JSON to dataset conversion',
                'error': str(e)
            })
        }

def create_dataset(json_content):
    # ここでJSONからデータセットを作成するロジックを実装
    # この例では、タイトル、見出し数、段落数、リンク数を特徴量としています
    dataset = [
        ['title', 'num_headings', 'num_paragraphs', 'num_links'],
        [
            json_content['title'],
            len(json_content['headings']),
            len(json_content['paragraphs']),
            len(json_content['links'])
        ]
    ]
    return dataset
```

4. 「設定」タブで、タイムアウトを3分に設定します。

## 4. S3イベント通知の設定

1. S3サービスに戻り、「hoge」バケットを選択します。
2. 「プロパティ」タブに移動し、「イベント通知」セクションを見つけます。
3. 「イベント通知の作成」をクリックします。
4. 以下の設定を行います：
   - イベント名: HTMLUploadTrigger
   - イベントタイプ: すべてのオブジェクト作成イベント
   - 接頭辞: html/
   - 送信先: Lambda関数
   - Lambda関数: HTML2JSONLambda
5. 「変更の保存」をクリックします。

## 5. テストと確認

1. テスト用のHTMLファイルを作成し、S3バケットの「html/」フォルダにアップロードします。
2. 数分待ち、「json/」フォルダに対応するJSONファイルが作成されたことを確認します。
3. 「機械学習/」フォルダに対応するCSVファイルが作成されたことを確認します。
4. Lambda関数のログ（CloudWatch Logs）を確認し、エラーがないことを確認します。

## 注意点

- 本番環境では、エラーハンドリングとログ記録をより強化することをお勧めします。
- セキュリティを考慮し、IAMロールの権限は必要最小限に絞ることをお勧めします。
- 大量のファイルを処理する場合は、Lambda関数のタイムアウト設定とメモリ割り当てを適切に調整してください。
- コストを考慮し、不要なリソースは削除するようにしてください。

以上の手順で、HTMLファイルがS3にアップロードされたときに自動的にJSONに変換し、さらにデータセットを作成するプロセスが完成します。