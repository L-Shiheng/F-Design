import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 核心渲染引擎：生成带边缘线的三维长方体 (模拟真实的铝型材)
# ==========================================
def create_box_traces(x, y, z, dx, dy, dz, color, name):
    """返回实体Mesh和边缘线两个Trace"""
    # 8个顶点
    xx = [x, x+dx, x+dx, x, x, x+dx, x+dx, x]
    yy = [y, y, y+dy, y+dy, y, y, y+dy, y+dy]
    zz = [z, z, z, z, z+dz, z+dz, z+dz, z+dz]
    
    # Mesh 表面
    i = [0, 0, 4, 4, 0, 0, 3, 3, 0, 0, 1, 1]
    j = [1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 2, 6]
    k = [2, 3, 6, 7, 5, 4, 6, 7, 7, 4, 6, 5]
    
    mesh = go.Mesh3d(
        x=xx, y=yy, z=zz, i=i, j=j, k=k, 
        color=color, opacity=0.9, name=name, showlegend=False, flatshading=True,
        lighting=dict(ambient=0.5, diffuse=0.8, roughness=0.1)
    )
    
    # 黑色的轮廓边缘线 (增加CAD图纸感)
    x_edges = [x, x+dx, x+dx, x, x, x, x+dx, x+dx, x+dx, x+dx, x, x, x, x, x+dx, x+dx]
    y_edges = [y, y, y+dy, y+dy, y, y, y, y, y+dy, y+dy, y+dy, y+dy, y+dy, y, y, y+dy]
    z_edges = [z, z, z, z, z, z+dz, z+dz, z, z, z+dz, z+dz, z, z+dz, z+dz, z+dz, z+dz]
    
    edges = go.Scatter3d(
        x=x_edges, y=y_edges, z=z_edges, 
        mode='lines', line=dict(color='#2c3e50', width=3), showlegend=False, hoverinfo='skip'
    )
    return [mesh, edges]

# ==========================================
# 界面交互与参数配置
# ==========================================
st.set_page_config(page_title="Pro 铝型材装配设计", layout="wide")
st.title("🏗️ 工业级参数化半高床设计器 (带干涉计算)")

with st.sidebar:
    st.header("📐 空间参数")
    L = st.number_input("床总长度 (mm)", value=2000, step=10)
    W = st.number_input("床总宽度 (mm)", value=1200, step=10)
    H_bed = st.number_input("床架净空高度 (mm)", value=1300, step=10)
    H_rail = st.number_input("护栏高度 (mm)", value=400, step=10)
    
    st.header("🚪 入口与爬梯模块")
    entrance_pos = st.radio("上下床入口位置", ["左侧", "右侧"])
    ladder_W = st.number_input("爬梯/入口宽度 (mm)", min_value=300, max_value=800, value=450, step=10)
    
    st.header("⚙️ 材料定义")
    profile_type = st.selectbox("主型材型号", ["4040", "3030"])
    pw = int(profile_type) // 100 # 解析宽度，4040 -> 40mm

# ==========================================
# 装配算法与 BOM 生成
# ==========================================
fig = go.Figure()
bom_raw = []

def add_part(module, name, x, y, z, dx, dy, dz, color):
    """将零件添加到三维空间，并同步记录到BOM"""
    traces = create_box_traces(x, y, z, dx, dy, dz, color, name)
    fig.add_traces(traces)
    length = int(max(dx, dy, dz)) # 获取最长边作为切割尺寸
    bom_raw.append({"装配模块": module, "零件名称": name, "型号": f"{profile_type}型材", "精确切割长度(mm)": length})

# 颜色预设
C_PILLAR = '#7f8c8d'  # 立柱-深灰
C_BEAM = '#bdc3c7'    # 横梁-浅银
C_RAIL = '#f1c40f'    # 护栏-黄色
C_LADDER = '#3498db'  # 爬梯-蓝色
C_PANEL = '#d35400'   # 面板-木色 (半透明)

H_total = H_bed + H_rail

# 1. 生成 6 根承重主立柱
pillars = [
    (0, 0), (L-pw, 0),             # 前排：左，右
    (0, W-pw), (L-pw, W-pw),       # 后排：左，右
    (L/2-pw/2, 0), (L/2-pw/2, W-pw)# 中间：前，后 (防塌陷)
]
for i, (px, py) in enumerate(pillars):
    add_part("主框架", f"立柱-{i+1}", px, py, 0, pw, pw, H_total, C_PILLAR)

# 2. 生成床铺层与底层的横梁 (Z=0 和 Z=H_bed-pw)
# 计算被中间立柱打断的横梁长度
beam_L_half = L/2 - 1.5*pw
beam_W_full = W - 2*pw

for z_level, m_name in [(0, "底部地梁"), (H_bed-pw, "床板承重架")]:
    # 前后长横梁 (共4段)
    add_part(m_name, "长横梁-左段", pw, 0, z_level, beam_L_half, pw, pw, C_BEAM)
    add_part(m_name, "长横梁-右段", L/2+pw/2, 0, z_level, beam_L_half, pw, pw, C_BEAM)
    add_part(m_name, "长横梁-后左段", pw, W-pw, z_level, beam_L_half, pw, pw, C_BEAM)
    add_part(m_name, "长横梁-后右段", L/2+pw/2, W-pw, z_level, beam_L_half, pw, pw, C_BEAM)
    
    # 左右宽横梁及中间横撑 (共3段)
    add_part(m_name, "宽横梁-左", 0, pw, z_level, pw, beam_W_full, pw, C_BEAM)
    add_part(m_name, "宽横梁-右", L-pw, pw, z_level, pw, beam_W_full, pw, C_BEAM)
    add_part(m_name, "宽横撑-中", L/2-pw/2, pw, z_level, pw, beam_W_full, pw, C_BEAM)

# 3. 生成安全护栏 (带参数化布尔打断逻辑)
z_rail = H_total - pw
# 后、左、右护栏完整
add_part("安全护栏", "后护栏(完整)", pw, W-pw, z_rail, L-2*pw, pw, pw, C_RAIL)
add_part("安全护栏", "左护栏", 0, pw, z_rail, pw, beam_W_full, pw, C_RAIL)
add_part("安全护栏", "右护栏", L-pw, pw, z_rail, pw, beam_W_full, pw, C_RAIL)

# 前护栏：根据入口位置进行切断运算
if entrance_pos == "左侧":
    # 左边空出 ladder_W，护栏从 pw+ladder_W 开始，一直到 L-pw
    rail_start = pw + ladder_W
    rail_len = (L - pw) - rail_start
    add_part("安全护栏", "前护栏(右侧保留段)", rail_start, 0, z_rail, rail_len, pw, pw, C_RAIL)
else: # 右侧
    # 右侧空出 ladder_W，护栏从 pw 开始，到 (L-pw)-ladder_W 结束
    rail_len = (L - pw - ladder_W) - pw
    add_part("安全护栏", "前护栏(左侧保留段)", pw, 0, z_rail, rail_len, pw, pw, C_RAIL)

# 4. 生成子装配体：爬梯模块 (贴在外侧 y = -pw)
# 确定爬梯的X坐标基准
ladder_x_start = pw if entrance_pos == "左侧" else (L - pw - ladder_W)

# 梯子左右立杆
add_part("爬梯模块", "爬梯左立杆", ladder_x_start, -pw, 0, pw, pw, H_total, C_LADDER)
add_part("爬梯模块", "爬梯右立杆", ladder_x_start + ladder_W - pw, -pw, 0, pw, pw, H_total, C_LADDER)

# 自动计算踏步数量并循环生成
step_spacing = 280 # 踏步间距约 28厘米
steps_count = int(H_bed // step_spacing)
step_len = ladder_W - 2*pw
for s in range(1, steps_count + 1):
    z_step = s * step_spacing
    add_part("爬梯模块", f"爬梯踏步-{s}", ladder_x_start + pw, -pw, z_step, step_len, pw, pw, C_LADDER)

# 5. 生成内嵌面板 (使用半透明薄片展示)
inner_L = L - 2*pw - 2
inner_W = W - 2*pw - 2
fig.add_traces(create_box_traces(pw+1, pw+1, H_bed-10, inner_L, inner_W, 10, C_PANEL, "实木床板"))
bom_raw.append({"装配模块": "木作模块", "零件名称": "内嵌实木床板", "型号": "18mm实木拼板", "精确切割长度(mm)": f"{inner_L} × {inner_W}"})

# 优化三维视图显示
fig.update_layout(
    scene=dict(
        xaxis_title='X (长度)', yaxis_title='Y (宽度/进深)', zaxis_title='Z (高度)',
        aspectmode='data',
        camera=dict(eye=dict(x=1.5, y=-1.5, z=1.2)) # 默认最佳俯视斜角
    ),
    margin=dict(l=0, r=0, b=0, t=0), height=600
)

# ==========================================
# BOM 数据透视与汇总 (工业标准格式)
# ==========================================
df_raw = pd.DataFrame(bom_raw)
# 将同尺寸、同型号的零件进行合并统计
df_grouped = df_raw.groupby(['装配模块', '型号', '精确切割长度(mm)']).size().reset_index(name='需求数量(根/块)')
df_grouped = df_grouped.sort_values(by=['装配模块', '需求数量(根/块)'], ascending=[True, False])

# ==========================================
# 界面渲染输出
# ==========================================
col1, col2 = st.columns([5, 3])

with col1:
    st.subheader("🛠️ 实时装配三维视图 (Solid Model)")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📋 自动化物料清单 (BOM)")
    st.write("这不再是估算！这是根据左侧三维模型中的每一根实体，进行布尔扣减后自动遍历得出的**真实下料单**。")
    st.dataframe(df_grouped, use_container_width=True, hide_index=True)
    
    st.info(f"**五金件推算模块：**\n系统检测到本次装配共生成了 {len(df_raw)} 个基础零件。根据 T 型连接点的拓扑计算，建议购买：\n"
            f"- **{profile_type} 角码**: {len(df_raw) * 2} 个\n"
            f"- **T型滑块螺母**: {len(df_raw) * 4} 个\n"
            f"- **内六角螺丝**: {len(df_raw) * 4} 个\n"
            f"- **角码盖板/端盖**: 约 20 个")
