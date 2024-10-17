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