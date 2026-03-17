import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 数据库预设 ---
PROFILES = {
    "3030型": {"width": 30, "max_load_kg": 150},
    "4040型": {"width": 40, "max_load_kg": 300},
    "4080型": {"width": 40, "max_load_kg": 600}, # 做床强烈建议主梁用4080
}

PANELS = {
    "实木拼板 (18mm)": {"desc": "结实环保，做床板或高档柜门"},
    "密度板/免漆板 (15mm)": {"desc": "性价比高，适合做床下储物柜的柜体"},
    "多层实木板 (18mm)": {"desc": "防潮性好，承重极佳，最适合做床板"}
}

def draw_loft_bed(L, W, H_clearance, H_guardrail):
    """专门绘制半高床的 3D 结构"""
    fig = go.Figure()
    H_total = H_clearance + H_guardrail
    
    # 6根立柱 (四个角 + 长边中间2根)
    mid_L = L / 2
    columns = [
        ([0, 0], [0, 0], [0, H_total]), ([L, L], [0, 0], [0, H_total]),
        ([L, L], [W, W], [0, H_total]), ([0, 0], [W, W], [0, H_total]),
        ([mid_L, mid_L], [0, 0], [0, H_total]), ([mid_L, mid_L], [W, W], [0, H_total]) # 中间两根
    ]
    for x, y, z in columns:
        fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color='#7f8c8d', width=8), showlegend=False))
    
    # 床铺主框架 (高度 = H_clearance)
    z_bed = H_clearance
    fig.add_trace(go.Scatter3d(x=[0, L, L, 0, 0], y=[0, 0, W, W, 0], z=[z_bed]*5, mode='lines', line=dict(color='#e74c3c', width=8), name="床铺主承重梁"))
    
    # 床板支撑横梁 (排骨架，简化画3根)
    for step in [L*0.25, L*0.5, L*0.75]:
        fig.add_trace(go.Scatter3d(x=[step, step], y=[0, W], z=[z_bed, z_bed], mode='lines', line=dict(color='#e74c3c', width=4), showlegend=False))

    # 护栏框架 (高度 = H_total)
    fig.add_trace(go.Scatter3d(x=[0, L, L, 0, 0], y=[0, 0, W, W, 0], z=[H_total]*5, mode='lines', line=dict(color='#f39c12', width=5), name="安全护栏"))
    
    # 床下储物柜基础框架 (贴地框架)
    fig.add_trace(go.Scatter3d(x=[0, L, L, 0, 0], y=[0, 0, W, W, 0], z=[0]*5, mode='lines', line=dict(color='#3498db', width=5), name="底部地梁(防变形)"))

    fig.update_layout(scene=dict(xaxis_title='长', yaxis_title='宽', zaxis_title='高', aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=500, showlegend=True)
    return fig

# --- 界面布局 ---
st.set_page_config(page_title="铝型材家具设计助手", layout="wide")
st.title("🧰 DIY 铝型材半高床生成器")

with st.sidebar:
    st.header("1. 半高床参数")
    L = st.number_input("床铺总长度 (mm)", value=2000, step=10)
    W = st.number_input("床铺总宽度 (mm)", value=1200, step=10)
    H_clearance = st.number_input("床下净空高度 (mm)", value=1200, step=10, help="决定了你下面能放多高的柜子")
    H_guardrail = st.number_input("顶层护栏高度 (mm)", value=350, step=10)
    
    st.header("2. 材料选择")
    profile_choice = st.selectbox("主框架铝型材", ["4040型", "4080型"], index=0, help="做床严禁使用2020或3030，必须4040起步！")
    panel_choice = st.selectbox("床板材质", list(PANELS.keys()), index=2)

# --- 计算逻辑 ---
profile_w = PROFILES[profile_choice]["width"]
bom_items = []
H_total = H_clearance + H_guardrail

# 1. 6根立柱 (非常关键)
bom_items.append({"部位": "主立柱", "配件名称": f"立柱 - {profile_choice}", "切割尺寸": f"{H_total} mm", "数量": 6, "备注": "四角4根，长边中段2根防塌"})

# 2. 承重主框架 (床铺那一层 + 底部地梁 + 顶部护栏)
# 扣除立柱厚度
l_len = L - (profile_w * 2)
w_len = W - (profile_w * 2)

# 长横梁：底部2根 + 床铺层2根 + 护栏2根 = 6根
bom_items.append({"部位": "横梁(长边)", "配件名称": f"长横梁 - {profile_choice}", "切割尺寸": f"{l_len} mm", "数量": 6, "备注": "地梁/床架/护栏"})
# 宽横梁：底部3根(含中间) + 床铺层3根(含中间) + 护栏2根 = 8根
bom_items.append({"部位": "横梁(宽边)", "配件名称": f"宽横梁 - {profile_choice}", "切割尺寸": f"{w_len} mm", "数量": 8, "备注": "地梁/床架/护栏"})

# 3. 床板支撑排骨架 (用4040横穿长边)
support_w_len = w_len # 宽度方向的横撑
bom_items.append({"部位": "床板支撑", "配件名称": "承重横撑 - 4040型", "切割尺寸": f"{support_w_len} mm", "数量": 4, "备注": "均布在床架下方支撑床板"})

# 4. 面板计算 (床板)
inner_L = L - (profile_w * 2) - 2
inner_W = W - (profile_w * 2) - 2
bom_items.append({"部位": "床板", "配件名称": f"主床板 ({panel_choice})", "切割尺寸": f"{inner_L} × {inner_W} mm", "数量": 1, "备注": "内嵌尺寸。太大的话建议让商家对半切成两块，方便搬运"})

# 5. 连接件
# 节点非常多，这里做一个估算：6个立柱 * 3层(底,中,顶) = 18个主要节点。每个节点至少2-3个角件
bracket_qty = 18 * 3 + 8 # 加上排骨架的连接件
bom_items.append({"部位": "五金件", "配件名称": f"{profile_choice} 强力角件", "切割尺寸": "标准", "数量": bracket_qty, "备注": "必须使用重型角件"})
bom_items.append({"部位": "五金件", "配件名称": "内六角螺栓+T型螺母", "切割尺寸": "配套尺寸", "数量": bracket_qty * 2, "备注": "宁多勿少"})

df_bom = pd.DataFrame(bom_items)

# --- 主界面展示 ---
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📐 半高床 3D 结构预览")
    fig = draw_loft_bed(L, W, H_clearance, H_guardrail)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("⚠️ 安全与工程警告")
    st.error("**承重警告：** 床是用来睡人的，存在动态载荷（翻身、上下床）。**绝对不能用 2020 或 3030 型材！** 建议立柱用 4040，承重主长梁用 4080（侧放）。")
    st.warning("**防倾倒警告：** 半高床重心极高！组装完成后，**必须使用膨胀螺丝或强力 L 型角码将靠近墙面的立柱与实体墙进行固定**，否则有严重的倾倒倒塌风险！")
    st.info("**关于下层储物柜：** 底部的蓝色和红色框架之间就是你的储物空间。你可以用 2020 型材或者直接用免漆板在里面组装独立的柜子，然后塞进去。")

st.divider()

st.subheader("🛒 半高床核心框架 BOM 清单")
st.dataframe(df_bom, use_container_width=True, hide_index=True)
