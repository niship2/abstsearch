# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st
from streamlit.logger import get_logger
from funcs.search import search
import pandas as pd
import requests
import json

LOGGER = get_logger(__name__)


def run():
    st.set_page_config(
        page_title="Hello",
        page_icon="👋",
        layout="wide"
    )

    st.write("臨時チャット検索")
    # APIエンドポイントとヘッダー
    API_URL = st.secrets["CHAT_URL"]
    HEADERS = {"Content-Type": "application/json"}

    st.title("Zuva Chat Streaming Demo 🚀")
    st.caption("臨時：Zuvaチャットを試せます")

    # --- メインコンテンツ ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("リクエスト設定")
        # ユーザーが質問を入力
        question_default = "宇宙で使える放熱技術を保有している企業を教えて"
        question = st.text_area(
            "質問を入力してください:", value=question_default, height=100)
        # スレッドIDもユーザーが入力できるようにする (デフォルト値を設定)
        thread_id_default = "thread_123"
        thread_id = st.text_input(
            "スレッドID:", value=thread_id_default, disabled=False)

    if st.button("送信してストリーミング表示", type="primary"):
        if not question:
            st.warning("質問を入力してください。")
        elif not thread_id:
            st.warning("スレッドIDを入力してください。")
        else:
            # APIリクエストのペイロード
            payload = {
                "question": question,
                "thread_id": thread_id
            }

            # st.info(
            #    f"APIにリクエストを送信中...\nURL: {API_URL}\nPayload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

            try:
                # ストリーミングでPOSTリクエストを送信
                # timeoutを設定 (connect, read)
                response = requests.post(
                    API_URL, headers=HEADERS, json=payload, stream=True, timeout=(30, 300))  # 接続10秒、読み取り300秒
                response.raise_for_status()  # HTTPエラーがあればここで例外発生

                # ストリーミングデータを表示するためのジェネレータ関数
                def generate_streamed_data():
                    for line in response.iter_lines(decode_unicode=True):  # 1行ずつ処理
                        if line:
                            try:
                                # 各行をJSONとしてパース
                                data = json.loads(line)
                                if "chunk" in data:
                                    # "chunk"キーの値を取得してyield
                                    yield data["chunk"]
                                elif data.get("done") is True:
                                    # {"done": true} を受信したら終了
                                    break
                            except json.JSONDecodeError:
                                # JSONとしてパースできない行は無視するか、エラーとして扱う
                                # 今回はAPI仕様に基づき、有効なJSONが来ることを期待
                                st.warning(f"JSONデコードエラー: スキップされた行: {line}")
                                pass  # またはエラー処理

                st.subheader("APIからのストリーミング応答:")
                # st.write_stream を使用してストリーミングデータを表示
                # このウィジェットは、ジェネレータから受け取った文字列を順次結合して表示します。
                # Markdownもレンダリングされます。
                with st.container(height=800, border=True):  # スクロール可能なコンテナ
                    st.write_stream(generate_streamed_data)

                st.success("ストリーミングが完了しました。")

            except requests.exceptions.HTTPError as http_err:
                st.error(f"HTTPエラーが発生しました: {http_err}")
                try:
                    # エラーレスポンスの内容を表示しようと試みる
                    error_content = response.text
                    st.error(f"エラーレスポンス内容: {error_content}")
                except Exception as e_text:
                    st.error(f"エラーレスポンスの読み取りに失敗しました: {e_text}")
            except requests.exceptions.ConnectionError as conn_err:
                st.error(f"接続エラーが発生しました: {conn_err}")
            except requests.exceptions.Timeout as timeout_err:
                st.error(f"タイムアウトエラーが発生しました: {timeout_err}")
            except requests.exceptions.RequestException as req_err:
                st.error(f"APIリクエストエラーが発生しました: {req_err}")
            except Exception as e:
                st.error(f"予期せぬエラーが発生しました: {e}")


if __name__ == "__main__":
    run()
