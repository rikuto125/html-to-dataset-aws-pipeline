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