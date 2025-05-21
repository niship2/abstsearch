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
# from funcs.search import search # 元のコードにありましたが、このスニペットでは未使用
import pandas as pd
import requests
import json
import io  # Excel出力に必要

LOGGER = get_logger(__name__)


# Excelファイルを作成してダウンロードするためのヘルパー関数
def to_excel(df):
    output = io.BytesIO()
    # DataFrameをExcelファイルとしてバイナリデータに変換
    # index=False でDataFrameのインデックスをExcelに出力しない
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='API応答')
    processed_data = output.getvalue()
    return processed_data


def run():
    st.set_page_config(
        page_title="Hello",
        page_icon="👋",
        layout="wide"
    )

    st.write("臨時チャット検索")
    # APIエンドポイントとヘッダー
    # st.secretsを使用するため、ローカル実行時は .streamlit/secrets.toml ファイルに CHAT_URL を設定してください
    if "CHAT_URL" not in st.secrets:
        st.error("エラー: CHAT_URLがsecretsに設定されていません。")
        st.stop()
    API_URL = st.secrets["CHAT_URL"]
    HEADERS = {"Content-Type": "application/json"}

    st.title("Zuva Chat Streaming Demo 🚀")
    st.caption("臨時：Zuvaチャットを試せます")

    # セッションステートでAPI応答を保持
    if "api_response_text" not in st.session_state:
        st.session_state.api_response_text = ""
    if "streaming_error" not in st.session_state:
        st.session_state.streaming_error = False

    # --- メインコンテンツ ---
    col1, col2 = st.columns(2)  # col2 は現状レイアウト上定義されていますが、主たる表示はcol1の下です

    with col1:
        st.subheader("リクエスト設定")
        question_default = "宇宙で使える放熱技術を保有している企業を教えて"
        question = st.text_area(
            "質問を入力してください:", value=question_default, height=100)
        thread_id_default = "thread_123"
        thread_id = st.text_input(
            "スレッドID:", value=thread_id_default, disabled=False)

    # API応答表示用のプレースホルダー
    response_placeholder = st.empty()
    # ダウンロードボタン表示用のプレースホルダー
    download_button_placeholder = st.empty()

    if st.button("送信してストリーミング表示", type="primary"):
        if not question:
            st.warning("質問を入力してください。")
        elif not thread_id:
            st.warning("スレッドIDを入力してください。")
        else:
            st.session_state.api_response_text = ""  # 送信時にリセット
            st.session_state.streaming_error = False  # エラーフラグもリセット
            download_button_placeholder.empty()  # 古いダウンロードボタンをクリア
            response_placeholder.empty()  # 古い応答表示をクリア

            payload = {
                "question": question,
                "thread_id": thread_id
            }

            try:
                # st.info(
                #    f"APIにリクエストを送信中...\nURL: {API_URL}\nPayload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
                response = requests.post(
                    API_URL, headers=HEADERS, json=payload, stream=True, timeout=(30, 300))
                response.raise_for_status()

                collected_chunks = []

                def generate_and_collect_streamed_data():
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            try:
                                data = json.loads(line)
                                if "chunk" in data:
                                    chunk = data["chunk"]
                                    collected_chunks.append(chunk)
                                    yield chunk
                                elif data.get("done") is True:
                                    break
                            except json.JSONDecodeError:
                                # ストリーミング中にJSONデコードエラーが発生した場合、エラーメッセージをyieldして表示
                                error_message = f"JSONデコードエラー: スキップされた行: {line}\n"
                                collected_chunks.append(
                                    error_message)  # エラー情報も収集
                                yield error_message
                                # st.warning(f"JSONデコードエラー: スキップされた行: {line}") # こちらはコンソールやUIに直接警告
                                pass

                with response_placeholder.container():
                    st.subheader("APIからのストリーミング応答:")
                    with st.container(height=800, border=True):
                        st.write_stream(generate_and_collect_streamed_data)

                st.session_state.api_response_text = "".join(collected_chunks)

                if not st.session_state.streaming_error and st.session_state.api_response_text:  # エラーがなく、テキストがある場合
                    st.success("ストリーミングが完了しました。")
                elif not st.session_state.streaming_error and not st.session_state.api_response_text:  # エラーがなく、テキストもない場合
                    st.info("ストリーミングは完了しましたが、表示するデータがありませんでした。")
                # エラーがある場合は、エラー処理ブロックでメッセージが表示される

            except requests.exceptions.HTTPError as http_err:
                st.session_state.streaming_error = True
                error_message = f"HTTPエラーが発生しました: {http_err}"
                try:
                    error_content = response.text  # responseオブジェクトが存在する場合
                    error_message += f"\nエラーレスポンス内容: {error_content}"
                except Exception as e_text:
                    error_message += f"\nエラーレスポンスの読み取りに失敗しました: {e_text}"
                response_placeholder.error(error_message)
                st.session_state.api_response_text = error_message
            except requests.exceptions.ConnectionError as conn_err:
                st.session_state.streaming_error = True
                error_message = f"接続エラーが発生しました: {conn_err}"
                response_placeholder.error(error_message)
                st.session_state.api_response_text = error_message
            except requests.exceptions.Timeout as timeout_err:
                st.session_state.streaming_error = True
                error_message = f"タイムアウトエラーが発生しました: {timeout_err}"
                response_placeholder.error(error_message)
                st.session_state.api_response_text = error_message
            except requests.exceptions.RequestException as req_err:
                st.session_state.streaming_error = True
                error_message = f"APIリクエストエラーが発生しました: {req_err}"
                response_placeholder.error(error_message)
                st.session_state.api_response_text = error_message
            except Exception as e:
                st.session_state.streaming_error = True
                error_message = f"予期せぬエラーが発生しました: {e}"
                response_placeholder.error(error_message)
                st.session_state.api_response_text = error_message

    # --- ダウンロードボタンの表示ロジック ---
    if st.session_state.api_response_text:
        lines = st.session_state.api_response_text.splitlines()
        # 空の行や空白のみの行を除外したい場合は、以下のコメントアウトを解除
        # lines = [line for line in lines if line.strip()]
        df = pd.DataFrame(lines, columns=["API応答"])

        if not df.empty:
            excel_data = to_excel(df)
            download_button_placeholder.download_button(
                label="応答をExcelファイルとしてダウンロード",
                data=excel_data,
                file_name="api_response.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        # api_response_text があっても df が空になるケースは通常ないが、念のため
        # (例えば、api_response_text が改行のみで構成される場合など。ただし splitlines() の挙動で通常は発生しにくい)
        elif not st.session_state.streaming_error:
            download_button_placeholder.info("ダウンロードする有効なデータがありません。")


if __name__ == "__main__":
    run()
