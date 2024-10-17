# HTML to Dataset AWS Pipeline

## 概要

HTML to Dataset AWS Pipelineは、S3バケットにアップロードされたHTMLファイルを自動的に処理し、JSONファイルに変換した後、機械学習用のデータセットを生成するAWSベースの自動化パイプラインです。

このプロジェクトは以下のコンポーネントで構成されています：

1. S3バケット：HTMLファイルの保存、中間JSONファイル、最終的なデータセットの保存
2. Lambda関数1 (HTML2JSON)：HTMLをJSONに変換
3. Lambda関数2 (JSON2Dataset)：JSONをCSV形式のデータセットに変換
4. IAMロール：必要な権限を付与
5. S3イベントトリガー：プロセスの自動化

## 機能

- HTMLファイルのS3バケットへのアップロードを自動検知
- HTMLファイルからJSONファイルへの変換
- JSONファイルから機械学習用データセット（CSV）の生成
- 各処理ステップの結果をS3バケットに保存

## 前提条件

- AWSアカウント
- AWS CLIのセットアップ（オプション、ただしデプロイメントに推奨）
- Python 3.12以上

## セットアップ

1. このリポジトリをクローンします：
   ```
   git clone https://github.com/yourusername/html-to-dataset-aws-pipeline.git
   ```

2. `setup/` ディレクトリ内のCloudFormationテンプレートを使用して、必要なAWSリソースを作成します。

3. Lambda関数のコードを `src/` ディレクトリからAWS Lambdaコンソールにアップロードします。

4. S3バケットのイベント通知を設定して、HTMLファイルのアップロード時にLambda関数をトリガーします。

詳細なセットアップ手順については、`docs/setup.md` を参照してください。

## 使用方法

1. 処理したいHTMLファイルをS3バケットの `html/` フォルダーにアップロードします。

2. 数分待つと、以下のファイルが自動的に生成されます：
   - `json/` フォルダー：HTMLから変換されたJSONファイル
   - `機械学習/` フォルダー：JSONから生成されたCSV形式のデータセット

3. 生成されたファイルを確認し、必要に応じて処理をカスタマイズします。

## カスタマイズ

- HTMLパース処理：`src/html_to_json.py` を編集
- データセット生成ロジック：`src/json_to_dataset.py` を編集

## トラブルシューティング

問題が発生した場合は、以下を確認してください：

1. CloudWatchログでLambda関数のエラーメッセージを確認
2. S3バケットの権限設定
3. IAMロールの権限設定


