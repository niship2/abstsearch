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

LOGGER = get_logger(__name__)


def add_url(text):
    fturl = "https://www.j-platpat.inpit.go.jp/cache/classify/patent/PMGS_HTML/jpp/F_TERM/ja/fTermList/fTermList" + text[0:5] +".html"
    return fturl

def run():
    st.set_page_config(
        page_title="Hello",
        page_icon="👋",
        layout="wide"
    )

    st.write("# Welcome to 検索式検索サイト👋")

    st.sidebar.text_area("予備")

    col1,col2 = st.columns([4,1])
    with col1:
        query = st.text_input("調べたい技術を入力",placeholder="自動運転時の手動と自動の切り替え")
    with col2:
        st.selectbox("検索対象",["Fターム","FI","IPC","CPC","USPC"])
    
    if st.button("検索"):
        st.sidebar.warning("１回目の実行は１分ほどかかります.")

        


        res = search(query)
        df = pd.DataFrame(res["response"])

        df["url"] = df["fterm"].apply(add_url)
        
        return_query = res["query"]
        st.write("クエリ："+return_query)
        st.dataframe(
        df,
        column_config={
        "url": st.column_config.LinkColumn("App URL"),
      },
      hide_index=True,
      )

        



if __name__ == "__main__":
    run()
