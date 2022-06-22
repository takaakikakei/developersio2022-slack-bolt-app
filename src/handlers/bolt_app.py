import json
import logging
import os
import re
from pprint import pformat
from typing import Dict

import boto3
from slack_bolt import Ack, App, Respond
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from slack_sdk import WebClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = App(
    process_before_response=True,
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_BOT_SIGNING_SECRET"],
)

home_tab_view = {
    "type": "home",
    "blocks": [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Tool"},
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "ツール実行申請",
                        "emoji": True,
                    },
                    "style": "primary",
                    "value": "create_task",
                    "action_id": "request_button_click",
                },
            ],
        },
    ],
}

request_modal_view = {
    "type": "modal",
    "callback_id": "request_modal",
    "title": {"type": "plain_text", "text": "ツール実行申請"},
    "submit": {"type": "plain_text", "text": "送信"},
    "close": {"type": "plain_text", "text": "閉じる"},
    "blocks": [
        {
            "type": "input",
            "block_id": "request-type-block",
            "element": {
                "type": "radio_buttons",
                "action_id": "input-element",
                "initial_option": {
                    "value": "tool_A",
                    "text": {"type": "plain_text", "text": "tool_A"},
                },
                "options": [
                    {
                        "value": "tool_A",
                        "text": {"type": "plain_text", "text": "tool_A"},
                    },
                    {
                        "value": "tool_B",
                        "text": {"type": "plain_text", "text": "tool_B"},
                    },
                ],
            },
            "label": {"type": "plain_text", "text": "実行するツール"},
        },
        {
            "type": "input",
            "block_id": "aws-account-id-block",
            "element": {"type": "plain_text_input", "action_id": "input-element"},
            "label": {"type": "plain_text", "text": "AWSアカウントID"},
        },
        {
            "type": "input",
            "block_id": "notes-block",
            "element": {
                "type": "plain_text_input",
                "action_id": "input-element",
                "multiline": True,
            },
            "label": {"type": "plain_text", "text": "備考欄"},
            "optional": True,
        },
    ],
}

approve_error_view = {
    "type": "modal",
    "callback_id": "approve_error_modal",
    "title": {"type": "plain_text", "text": "承認エラー"},
    "close": {"type": "plain_text", "text": "キャンセル"},
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "承認エラーです。",
            },
        },
    ],
}


def make_request_message(
    approver_user_id: str,
    click_user_id: str,
    aws_account_id: str,
    request_type: str,
    notes: str,
):
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "ツール実行承認依頼"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"To：<@{approver_user_id}>\n"
                    f"From：<@{click_user_id}>\n"
                    "下記ツール実行の承認をお願いします:bow:"
                ),
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*ツール名:*\n{request_type}"},
                {"type": "mrkdwn", "text": f"*AWSアカウントID:*\n{aws_account_id}"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (f"```{notes}```"),
            },
        },
        {
            "type": "actions",
            "block_id": "request-status-block",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Approve",
                        "emoji": True,
                    },
                    "value": "approved",
                    "style": "primary",
                    "action_id": "approve_button_click",
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Deny",
                        "emoji": True,
                    },
                    "confirm": {
                        "title": {"type": "plain_text", "text": "差戻確認"},
                        "text": {
                            "type": "mrkdwn",
                            "text": "この申請を本当に差戻しますか?\n差戻後は元に戻すことはできません。",
                        },
                        "confirm": {"type": "plain_text", "text": "Do it"},
                        "deny": {
                            "type": "plain_text",
                            "text": "Cancel",
                        },
                    },
                    "value": "denied",
                    "style": "danger",
                    "action_id": "denied_button_click",
                },
            ],
        },
    ]


def respond_to_slack_within_3_seconds(ack):
    """
    Lazy listeners機能の使用時に、3秒以内にレスポンスを返す処理
    """
    ack()


"""
ホームタブのviewを表示
"""


@app.event("app_home_opened")
def update_home_tab(client: WebClient, event: Dict):

    try:
        client.views_publish(user_id=event["user"], view=home_tab_view)
    except Exception as e:
        logger.error(f"Error publishing home tab:\n {e}")


"""
ホームタブのツール実行ボタンを押したときの処理
Lazy listenersを利用
"""


def handle_open_modal_button_clicks(
    body: Dict,
    client: WebClient,
):
    """
    ツール実行申請ボタンを押したときの処理
    """
    client.views_open(
        trigger_id=body["trigger_id"],
        view=request_modal_view,
    )


app.action("request_button_click")(
    ack=respond_to_slack_within_3_seconds,
    lazy=[handle_open_modal_button_clicks],
)

"""
モーダルの入力情報を取り出し
"""


@app.view("request_modal")
def handle_request_modal_view_events(
    ack: Ack, body: Dict, view: Dict, client: WebClient
):
    inputs = view["state"]["values"]
    aws_account_id = (
        inputs.get("aws-account-id-block", {}).get("input-element", {}).get("value")
    )
    request_type = (
        inputs.get("request-type-block", {})
        .get("input-element", {})
        .get("selected_option", {})
        .get("value")
    )
    notes = inputs.get("notes-block", {}).get("input-element", {}).get("value")

    """
    バリデーション
    - aws_account_id は12桁数値からなる文字列のみ許可
    """

    pattern = "^[0-9]{12}$"
    if not re.compile(pattern).match(aws_account_id):
        ack(
            response_action="errors",
            errors={
                "aws-account-id-block": "12桁の数値を入力してください",
            },
        )
        return

    """
    メッセージ送信
    """
    if notes is None:
        notes = "備考なし"
    approver_user_id = os.environ["APPRPOVER_USER_ID"]
    click_user_id = body["user"]["id"]
    try:
        client.chat_postMessage(
            channel=os.environ["APPROVAL_REQUEST_CHANNEL_ID"],
            blocks=make_request_message(
                approver_user_id,
                click_user_id,
                aws_account_id,
                request_type,
                notes,
            ),
            text="ツール実行確認依頼",
        )
    except Exception as e:
        logger.exception(f"Failed to post a message {e}")

    # 空の応答はこのモーダルを閉じる（ここまで 3 秒以内である必要あり）
    ack()


"""
Approveボタンを押したときの処理
Lazy listenersを利用
"""


def approve_request(body: Dict, respond: Respond, client: WebClient):
    # ボタン押下したユーザーが承認者のみ後続の処理に進む
    click_user_id = body["user"]["id"]
    approver_users = [os.environ["APPRPOVER_USER_ID"]]
    if not click_user_id in approver_users:
        client.views_open(
            trigger_id=body["trigger_id"],
            view=approve_error_view,
        )
        logger.info(f"{click_user_id} is not approver")
        return

    # 選択されたツール用のステートマシン実行
    selected_tool = body["message"]["blocks"][2]["fields"][0]["text"]
    if "tool_A" in selected_tool:
        extract_statemachine_arn = os.environ["TOOL_A_STATEMACHINE_ARN"]
    elif "tool_B" in selected_tool:
        extract_statemachine_arn = os.environ["TOOL_B_STATEMACHINE_ARN"]
    else:
        logger.error(f"Unexpected tool is seleted:\n{selected_tool}")
        return

    try:
        sfn_client = boto3.client("stepfunctions", region_name=os.environ["AWS_REGION"])
        message = {}
        res = sfn_client.start_execution(
            stateMachineArn=extract_statemachine_arn, input=json.dumps(message)
        )
        executionArn = res["executionArn"]
        logger.info(f"executionArn:\n {executionArn}")
    except Exception as e:
        logger.error(e)
        return

    # 実行メッセージ送信
    respond(
        blocks=[
            body["message"]["blocks"][0],
            body["message"]["blocks"][1],
            body["message"]["blocks"][2],
            body["message"]["blocks"][3],
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<@{click_user_id}>さんが承認して実行しました。",
                },
            },
        ]
    )


app.action("approve_button_click")(
    ack=respond_to_slack_within_3_seconds,
    lazy=[approve_request],
)


"""
Denyボタンを押したときの処理
Lazy listenersを利用
"""


def denied_request(body: Dict, respond: Respond):
    click_user_id = body["user"]["id"]

    respond(
        blocks=[
            body["message"]["blocks"][0],
            body["message"]["blocks"][1],
            body["message"]["blocks"][2],
            body["message"]["blocks"][3],
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<@{click_user_id}>さんが差戻しました。",
                },
            },
        ]
    )


app.action("denied_button_click")(
    ack=respond_to_slack_within_3_seconds,
    lazy=[denied_request],
)

"""
Slack Appのエントリポイント
"""


def handler(event, context):
    logger.info(f"event:\n{pformat(event)}")
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)
