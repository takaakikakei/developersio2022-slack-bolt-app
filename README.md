# developersio2022-slack-bolt-app

クラスメソッド株式会社がオンライン開催する、DevelopersIO 2022 でのセッション用のデモアプリです。

# デプロイ方法

## 事前準備

初回実行時に必要な準備を記載します。既に設定済のものはスキップしてください。

### npm

端末に npm をインストールします。

- [Configuring your local environment | npm](https://docs.npmjs.com/getting-started/configuring-your-local-environment)

簡単にですが、Homebrew から npm をインストールする例を紹介しています。

[Serverless Framework 用の端末設定メモ | Takaaki Kakei](https://zenn.dev/t_kakei/scraps/8675d5b86ffc4f)

### Pipenv

端末に Pipenv をインストールします。

- [さぁ今すぐこれから Pipenv をインストール! | Pipenv](https://pipenv-ja.readthedocs.io/ja/translate-ja/#install-pipenv-today)

以下は、Homebrew でインストールする場合のコマンド例です。

```bash
$ brew install pipenv
```

### Serverless Framework

端末に Serverless Framework をインストールします。

- [Setting Up Serverless Framework With AWS | Serverless](https://www.serverless.com/framework/docs/getting-started)

以下は、npm でインストールする場合のコマンド例です。

```bash
$ npm install -g serverless
```

デプロイ先の AWS 環境で、Serverless Framework が利用する IAM ユーザーとアクセスキーを作成します。
また端末で、デプロイ時に利用する AWS プロファイルの設定をします。

- [AWS Credentials | Serverless](https://www.serverless.com/framework/docs/providers/aws/guide/credentials)

なお、AWS プロファイルは AWS Vault で管理することを推奨します。

- [AWS Vault で端末内の AWS アクセスキー平文保存をやめてみた](https://dev.classmethod.jp/articles/aws-vault/)

## 端末でのプロジェクトのセットアップ

```bash
$ git@github.com:takaakikakei/developersio2022-slack-bolt-app.git
$ cd developersio2022-slack-bolt-app.git
$ npm ci # 必要なプラグインのインストール
$ pipenv install # 必要なパッケージのインストール
```

## Slack App の作成

### Slack App の作成

### AWS Systems Manager の設定

Slack App のクレデンシャル情報はコード内に直接書きたくないので、
AWS Systems Manager のパラメータストアに保存しておきます。
パラメータ名はそれぞれ以下で保存します。

- Bot User OAuth Token

```bash
/developersio2022-slack-bolt-app/dev/SLACK_BOT_TOKEN
# /サービス名/ステージ名/SLACK_BOT_TOKEN
```

- Signing Secret

```bash
/developersio2022-slack-bolt-app/dev/SLACK_BOT_SIGNING_SECRET
# /サービス名/ステージ名/SLACK_BOT_SIGNING_SECRET
```

## プロジェクトのデプロイ

プロジェクトのディレクトリで以下のコマンドでデプロイします。

```bash
aws-vault exec pte -- sls deploy --stage dev
# aws-vault exec プロファイル名 -- sls deploy --stage ステージ名
```

AWS Vault を利用しない場合は、以下のようなコマンドになります。

```bash
sls deploy --stage dev --profile pte
# sls deploy --stage ステージ名 --profile プロファイル名
```

これでデプロイ完了です。お疲れ様でした！
