import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random
import os

st.set_page_config(page_title="北京流浪动物寻家地图", layout="wide", page_icon="🐾")

# ================= 简易登录系统 =================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# 侧边栏最底部管理员登录扩展
with st.sidebar.expander("🔐 管理员登录通道"):
    if not st.session_state["logged_in"]:
        pwd = st.text_input("请输入管理密码:", type="password")
        if st.button("登录"):
            if pwd == "admin123":  # 默认密码
                st.session_state["logged_in"] = True
                st.success("登录成功！")
                st.rerun()
            else:
                st.error("密码错误")
    else:
        st.write("✨ 已进入管理员模式")
        if st.button("退出登录"):
            st.session_state["logged_in"] = False
            st.rerun()

# ================= 主页面结构 =================
st.title("北京流浪动物寻家地图 📍")
st.markdown("##### *每一个饱经风霜的小生命，都在等一个温暖的家。*")
st.write("---")

# 北京各行政区中心经纬度字典
BEIJING_DISTRICTS = {
    "东城区": [39.9284, 116.4166], "西城区": [39.9123, 116.3657], "朝阳区": [39.9215, 116.4864],
    "海淀区": [39.9599, 116.2981], "丰台区": [39.8584, 116.2872], "石景山区": [39.9065, 116.2230],
    "门头沟区": [39.9404, 115.9327], "房山区": [39.7415, 115.9754], "通州区": [39.9110, 116.6572],
    "顺义区": [40.1301, 116.6542], "昌平区": [40.2202, 116.2312], "大兴区": [39.7265, 116.3415],
    "平谷区": [40.1407, 117.1213], "怀柔区": [40.3162, 116.6321], "密云区": [40.3768, 116.8431],
    "延庆区": [40.4572, 115.9750]
}

def get_age_bucket(age_str):
    age_str = str(age_str)
    if "个月" in age_str or "天" in age_str: return "幼年 (1岁以下)"
    if "1岁" in age_str or "2岁" in age_str: return "青年 (1-2岁)"
    if "3岁" in age_str or "4岁" in age_str or "5岁" in age_str or "6岁" in age_str: return "成年 (3-6岁)"
    if "岁" in age_str: return "老年 (7岁以上)"
    return "未知"

# 锁死绝对路径
excel_file = r"C:\Users\by_ca\Projects\beijing-cow-cat-adoption\cats.xlsx"
if not os.path.exists(excel_file):
    excel_file = r"C:\Users\by_ca\Projects\beijing-cow-cat-adoption\cats.xlsx.xlsx"

if not os.path.exists(excel_file):
    st.error("❌ 未找到数据文件 cats.xlsx")
else:
    df = pd.read_excel(excel_file).fillna("未填写")
    df.columns = df.columns.astype(str).str.strip()

    # 标准列名绑定
    name_col = "Name (姓名)" if "Name (姓名)" in df.columns else df.columns[0]
    species_col = "Species (物种)" if "Species (物种)" in df.columns else None
    breed_col = "Pattern (花色)" if "Pattern (花色)" in df.columns else None
    gender_col = "Gender (性别)" if "Gender (性别)" in df.columns else None
    age_col = "Age (年龄)" if "Age (年龄)" in df.columns else None
    spay_col = "Spay/Neuter (绝育)" if "Spay/Neuter (绝育)" in df.columns else None
    vac_col = "Vaccine (免疫)" if "Vaccine (免疫)" in df.columns else None
    coord_col = "Beijing District (坐标)" if "Beijing District (坐标)" in df.columns else None
    remark_col = "Temperament & Notes (性格与备注)" if "Temperament & Notes (性格与备注)" in df.columns else None
    contact_col = "Contact (联系人)" if "Contact (联系人)" in df.columns else None
    wechat_col = "WeChat ID (微信号)" if "WeChat ID (微信号)" in df.columns else None
    photo_col = next((c for c in df.columns if "Photo" in c or "图片" in c), None)

    # 提炼区域与年龄
    df["Clean_District"] = df[coord_col].apply(lambda x: next((d for d in BEIJING_DISTRICTS.keys() if d in str(x)), "其他"))
    df["Age_Bucket"] = df[age_col].apply(get_age_bucket)

    # 管理员后台展示
    if st.session_state["logged_in"]:
        st.markdown("### 🛠️ 数据维护面板（仅管理员可见）")
        st.dataframe(df[[name_col, species_col, gender_col, coord_col]], use_container_width=True)
        st.write("---")

    # 侧边栏高级筛选
    st.sidebar.header("高级筛选 🔍")
    sel_species = st.sidebar.selectbox("1. 选择物种:", ["全部"] + list(df[species_col].unique()) if species_col else ["全部"])
    sel_gender = st.sidebar.selectbox("2. 选择性别:", ["全部", "男生", "女生"])
    sel_district = st.sidebar.selectbox("3. 选择区域 (北京各区):", ["全部"] + list(BEIJING_DISTRICTS.keys()))
    sel_age = st.sidebar.selectbox("4. 选择年龄段:", ["全部", "幼年 (1岁以下)", "青年 (1-2岁)", "成年 (3-6岁)", "老年 (7岁以上)"])

    # 【完美修复】精准数据过滤
    f_df = df.copy()
    if sel_species != "全部" and species_col: f_df = f_df[f_df[species_col].str.strip() == sel_species]
    if sel_gender != "全部" and gender_col: f_df = f_df[f_df[gender_col].str.strip() == sel_gender]
    if sel_district != "全部": f_df = f_df[f_df["Clean_District"] == sel_district]
    if sel_age != "全部": f_df = f_df[f_df["Age_Bucket"] == sel_age]

    # 看板
    c1, c2, c3 = st.columns(3)
    c1.metric("展示总数", f"{len(f_df)} 只")
    c2.metric("男生数量", f"{len(f_df[f_df[gender_col].str.strip()=='男生'] if gender_col else [])} 只")
    c3.metric("女生数量", f"{len(f_df[f_df[gender_col].str.strip()=='女生'] if gender_col else [])} 只")

    # 初始化高德地图
    m = folium.Map(location=[39.9042, 116.4074], zoom_start=10, tiles='http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', attr='AutoNavi')

    for idx, row in f_df.iterrows():
        d_name = row["Clean_District"]
        if d_name in BEIJING_DISTRICTS:
            base_lat, base_lng = BEIJING_DISTRICTS[d_name]
            lat = base_lat + random.uniform(-0.015, 0.015)
            lng = base_lng + random.uniform(-0.015, 0.015)

            s_type = str(row[species_col]).strip() if species_col else "猫"
            is_dog = "狗" in s_type or "犬" in s_type

            # 跳过微信公众号防盗链链接，其余有效网络图片正常展示
            p_url = str(row.get(photo_col, "未填写")).strip() if photo_col else "未填写"
            if "http" in p_url and "qpic.cn" not in p_url:
                image_html = f'<div style="width: 100%; height: 130px; overflow: hidden; border-radius: 6px; margin-bottom: 8px;"><img src="{p_url}" style="width: 100%; height: 100%; object-fit: cover;"></div>'
            else:
                image_html = ""

            popup_html = f"""
            <div style="font-family: 'Microsoft YaHei'; width: 220px; font-size: 13px; line-height: 1.5;">
                {image_html}
                <h4 style="color: #FF5A5F; margin: 0 0 6px 0;">🐾 [{s_type}] {row[name_col]}</h4>
                <b>性别/年龄:</b> {row[gender_col]} / {row[age_col]}<br>
                <b>绝育/免疫:</b> {row[spay_col]} / {row[vac_col]}<br>
                <b>位置:</b> {row[coord_col]}<br>
                <p style="color: #555; font-size: 12px; margin: 6px 0;"><b>性格备注:</b> {row[remark_col]}</p>
                <div style="background: #F7F7F7; padding: 6px; border-radius: 4px; font-size: 12px;">
                    🤝 <b>联系:</b> {row[contact_col]} <br> 💬 <b>微信:</b> {row[wechat_col]}
                </div>
            </div>
            """
            
            g_val = str(row[gender_col]).strip()
            icon_name = "dog" if is_dog else "cat"
            icon_color = "cadetblue" if g_val == "男生" else "pink"
            
            folium.Marker(
                location=[lat, lng], 
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa")
            ).add_to(m)

    st_folium(m, width="100%", height=600, returned_objects=[])