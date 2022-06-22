# developersio2022-slack-bolt-app

クラスメソッド株式会社がオンライン開催する、DevelopersIO 2022 でのセッション用のデモアプリです。

# このアプリでできること

主に以下のことができます。

- ホームタブの表示
- ホームタブ上のボタンからモーダルの表示
- モーダルのバリデーション
- モダールの情報を元にチャンネルにメッセージ送信
- メッセージ上のボタンから、AWS Step Functions のステートマシン起動
- メッセージ上のボタンから元のメッセージを書き換え

# セットアップ手順

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

---

## 端末でのプロジェクトのセットアップ

```bash
$ git@github.com:takaakikakei/developersio2022-slack-bolt-app.git
$ cd developersio2022-slack-bolt-app.git
$ npm ci # 必要なプラグインのインストール
$ pipenv install # 必要なパッケージのインストール
```

---

## Slack App の準備

### Slack App の作成

- [Your Apps](https://api.slack.com/apps)から `Create New App` を選択
- `Create New App` のポップアップが表示されたら、`From scratch` を選択
- `Name app & choose workspace` のポップアップが表示されたら、アプリ名とインストール先のワークスペースを入力

### App Manifest

`App Manifest` を開いて、以下のように yml を設定します。

```yml
display_information:
  name: DevelopersIO2022 PoC App
  description: DevelopersIO2022のプレゼン用アプリ
  background_color: '#004492'
features:
  app_home:
    home_tab_enabled: true
    messages_tab_enabled: false
    messages_tab_read_only_enabled: true
  bot_user:
    display_name: devio2022_poc_app
    always_online: true
oauth_config:
  scopes:
    bot:
      - channels:history
      - groups:history
      - chat:write
settings:
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```

### OAuth & Permissions

- `OAuth & Permissions` を開いて、`OAuth Tokens for Your Workspace` で `Install to WorkSpace`をクリックしてインストール
- `Bot User OAuth Token` をメモしておく

### Basic Information

- `Basic Information` を開いて、`Signing Secret` をメモしておく

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

---

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

デプロイ完了すると、Amazon API Gateway のエンドポイントが表示されるのでメモしておきます。

---

## Slack App にエンドポイントを設定

### Interactivity & Shortcuts の設定

- Slack App の `Interactivity & Shortcuts` を開きます
- `Interactivity` を On にします
- `Request URL` に Amazon API Gateway のエンドポイントを設定します

### Event Subscriptions の設定

- Slack App の `Event Subscriptions` を開きます
- `Enable Events` を On にします
- `Request URL` に Amazon API Gateway のエンドポイントを設定します
- `Subscribe to bot events` で以下のイベントを許可します
  - app_home_opened
  - message.channels
  - message.groups

---

## ワークスペース上でアプリの追加

- Slack ワークスペースを開き、画面の左ペインの、`App` → `アプリの追加` から、対象のアプリをインストールします
- メッセージを投稿するチャンネルにアプリを追加します

---

これでセットアップ完了です。お疲れ様でした！
