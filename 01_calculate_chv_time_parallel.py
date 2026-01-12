import os
import numpy as np
import rasterio
from scipy.spatial import ConvexHull
import glob
import time
import multiprocessing as mp
from tqdm import tqdm

# 定义输入和输出路径
INPUT_PATH = r'D:\背景值处理_2m'
OUTPUT_PATH = r'D:\背景值处理_2m\CHV_2m_time_parallel'

# 并行配置
NUM_PROCESSES = 4     # 并行处理的时间点/时间段数（减少以避免资源竞争）
BLOCK_SIZE = 200      # 块大小（行数，减小以降低内存压力）

# 创建输出目录
os.makedirs(OUTPUT_PATH, exist_ok=True)

# 获取所有指标名称
def get_all_indices():
    mt_path = os.path.join(INPUT_PATH, 'MTs')
    indices = [d for d in os.listdir(mt_path) if os.path.isdir(os.path.join(mt_path, d))]
    return sorted(indices)

# 获取MTs的所有日期
def get_mt_dates():
    mt_path = os.path.join(INPUT_PATH, 'MTs')
    indices = get_all_indices()
    if not indices:
        return []
    
    idx = indices[0]
    idx_path = os.path.join(mt_path, idx)
    files = glob.glob(os.path.join(idx_path, '*.tif'))
    dates = sorted([os.path.basename(f).split('_')[0] for f in files])
    return dates

# 获取STMs的所有周期
def get_stm_periods():
    stm_path = os.path.join(INPUT_PATH, 'STMs')
    periods = [d for d in os.listdir(stm_path) if os.path.isdir(os.path.join(stm_path, d))]
    return sorted(periods)

# 获取STMs的所有统计类型
def get_stm_stats():
    stm_path = os.path.join(INPUT_PATH, 'STMs')
    periods = get_stm_periods()
    if not periods:
        return []
    
    period = periods[0]
    period_path = os.path.join(stm_path, period)
    indices = [d for d in os.listdir(period_path) if os.path.isdir(os.path.join(period_path, d))]
    
    if not indices:
        return []
    
    idx = indices[0]
    idx_path = os.path.join(period_path, idx)
    files = glob.glob(os.path.join(idx_path, '*.tif'))
    # 正确提取统计类型：先去掉扩展名，再split获取倒数第二个元素
    stats = sorted(list(set([os.path.splitext(os.path.basename(f))[0].split('_')[-2] for f in files])))
    return stats

# 处理单个MTs日期的多维CHV计算
def process_single_mt_date(date):
    """
    处理单个MTs日期的多维CHV计算
    输入：单个日期
    输出：CHV结果文件
    """
    print(f'\n=== 开始处理MTs日期 {date} ===')
    
    # 获取所有指标
    indices = get_all_indices()
    
    # 收集该日期下所有指标的数据
    all_data = []
    valid_indices = []
    
    for idx in indices:
        file_path = os.path.join(INPUT_PATH, 'MTs', idx, f'{date}_{idx}.tif')
        if not os.path.exists(file_path):
            print(f'  ✗ 未找到文件: {file_path}')
            continue
        
        print(f'  ✓ 读取文件: {os.path.basename(file_path)}')
        
        with rasterio.open(file_path) as src:
            data = src.read(1)
            
            # 处理nodata值
            if src.nodatavals[0] is not None:
                data[data == src.nodatavals[0]] = np.nan
            
            # 处理常见的nodata值
            data[data == -9999.0] = np.nan
            data[data == -9999] = np.nan
            data[data == 9999.0] = np.nan
            data[data == 9999] = np.nan
            
            # 添加极端值过滤（范围：-2000 到 2000）
            data[data < -2000] = np.nan
            data[data > 2000] = np.nan
            
            all_data.append(data)
            valid_indices.append(idx)
    
    if not all_data:
        print(f'  ✗ 未找到有效数据')
        return False, None
    
    print(f'  ✓ 成功读取 {len(valid_indices)} 个指标的数据')
    
    # 获取示例文件的profile
    sample_file = os.path.join(INPUT_PATH, 'MTs', valid_indices[0], f'{date}_{valid_indices[0]}.tif')
    with rasterio.open(sample_file) as src:
        sample_profile = src.profile
    
    # 获取数据尺寸
    total_height, width = all_data[0].shape
    
    # 计算块数
    num_blocks = (total_height + BLOCK_SIZE - 1) // BLOCK_SIZE
    
    print(f'  数据尺寸: {total_height}x{width}')
    print(f'  块数: {num_blocks}, 块大小: {BLOCK_SIZE}')
    print(f'  维度数: {len(all_data)} (使用{len(valid_indices)}个指标)')
    
    # 堆叠数据 (维度数 × 高度 × 宽度)
    stacked_data = np.stack(all_data, axis=0)
    
    # 准备输出文件
    output_file = os.path.join(OUTPUT_PATH, f'CHV_MTs_{date}.tif')
    
    profile = sample_profile.copy()
    profile.update({
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1,
        'nodata': np.nan
    })
    
    # 串行处理所有块
    print(f'  开始串行处理块...')
    
    # 创建输出文件
    with rasterio.open(output_file, 'w', **profile) as dst:
        for block_idx in tqdm(range(num_blocks), desc=f'    处理块', leave=False):
            start_row = block_idx * BLOCK_SIZE
            end_row = min((block_idx + 1) * BLOCK_SIZE, total_height)
            block_height = end_row - start_row
            
            if block_height <= 0:
                continue
            
            # 初始化块结果
            chv_block = np.full((block_height, width), np.nan, dtype=np.float32)
            
            # 计算CHV
            total_pixels = block_height * width
            processed = 0
            
            for i in range(block_height):
                if i % 100 == 0:  # 每处理100行显示一次进度
                    print(f'      行 {i}/{block_height}, 已处理 {processed}/{total_pixels} 像素')
                    
                for j in range(width):
                    processed += 1
                    
                    # 获取该像素的所有指标值
                    pixel_values = stacked_data[:, start_row + i, j]
                    valid_values = pixel_values[~np.isnan(pixel_values)]
                    
                    if len(valid_values) < 2:
                        continue
                        
                    try:
                        # 优化：直接计算max-min，避免复杂的ConvexHull计算
                        # 对于单个像素的18个指标值（1D空间中的点集），
                        # 凸包体积等价于最大值减去最小值
                        chv_block[i, j] = np.max(valid_values) - np.min(valid_values)
                    except Exception as e:
                        # 计算失败时保持NaN
                        continue
            
            # 写入块结果
            dst.write(chv_block, 1, window=rasterio.windows.Window(0, start_row, width, block_height))
    
    print(f'✓ 完成MTs日期 {date}，结果保存在: {output_file}')
    return True, output_file

# 处理单个STMs周期和统计类型的多维CHV计算
def process_single_stm_period(period, stat):
    """
    处理单个STMs周期和统计类型的多维CHV计算
    输入：周期和统计类型
    输出：CHV结果文件
    """
    print(f'\n=== 开始处理STMs周期 {period}，统计类型 {stat} ===')
    
    # 获取所有指标
    indices = get_all_indices()
    
    # 收集该周期和统计类型下所有指标的数据
    all_data = []
    valid_indices = []
    
    for idx in indices:
        file_path = os.path.join(INPUT_PATH, 'STMs', period, idx, f'{period}_{idx}_{stat}_masked.tif')
        if not os.path.exists(file_path):
            print(f'  ✗ 未找到文件: {file_path}')
            continue
        
        print(f'  ✓ 读取文件: {os.path.basename(file_path)}')
        
        with rasterio.open(file_path) as src:
            data = src.read(1)
            
            # 处理nodata值
            if src.nodatavals[0] is not None:
                data[data == src.nodatavals[0]] = np.nan
            
            # 处理常见的nodata值
            data[data == -9999.0] = np.nan
            data[data == -9999] = np.nan
            data[data == 9999.0] = np.nan
            data[data == 9999] = np.nan
            
            # 添加极端值过滤（范围：-2000 到 2000）
            data[data < -2000] = np.nan
            data[data > 2000] = np.nan
            
            all_data.append(data)
            valid_indices.append(idx)
    
    if not all_data:
        print(f'  ✗ 未找到有效数据')
        return False, None
    
    print(f'  ✓ 成功读取 {len(valid_indices)} 个指标的数据')
    
    # 获取示例文件的profile
    sample_file = os.path.join(INPUT_PATH, 'STMs', period, valid_indices[0], f'{period}_{valid_indices[0]}_{stat}_masked.tif')
    with rasterio.open(sample_file) as src:
        sample_profile = src.profile
    
    # 获取数据尺寸
    total_height, width = all_data[0].shape
    
    # 计算块数
    num_blocks = (total_height + BLOCK_SIZE - 1) // BLOCK_SIZE
    
    print(f'  数据尺寸: {total_height}x{width}')
    print(f'  块数: {num_blocks}, 块大小: {BLOCK_SIZE}')
    print(f'  维度数: {len(all_data)} (使用{len(valid_indices)}个指标)')
    
    # 堆叠数据 (维度数 × 高度 × 宽度)
    stacked_data = np.stack(all_data, axis=0)
    
    # 准备输出文件
    output_file = os.path.join(OUTPUT_PATH, f'CHV_STMs_{period}_{stat}.tif')
    
    profile = sample_profile.copy()
    profile.update({
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1,
        'nodata': np.nan
    })
    
    # 串行处理所有块
    print(f'  开始串行处理块...')
    
    # 创建输出文件
    with rasterio.open(output_file, 'w', **profile) as dst:
        for block_idx in tqdm(range(num_blocks), desc=f'    处理块', leave=False):
            start_row = block_idx * BLOCK_SIZE
            end_row = min((block_idx + 1) * BLOCK_SIZE, total_height)
            block_height = end_row - start_row
            
            if block_height <= 0:
                continue
            
            # 初始化块结果
            chv_block = np.full((block_height, width), np.nan, dtype=np.float32)
            
            # 计算CHV
            for i in range(block_height):
                for j in range(width):
                    # 获取该像素的所有指标值
                    pixel_values = stacked_data[:, start_row + i, j]
                    valid_values = pixel_values[~np.isnan(pixel_values)]
                    
                    if len(valid_values) < 2:
                        continue
                        
                    try:
                        # 对于1D数据（单像素多指标），直接使用最大值-最小值
                        # 这与ConvexHull.volume等价，但计算效率更高
                        # 优化：直接计算max-min，避免复杂的ConvexHull计算
                        chv_block[i, j] = np.max(valid_values) - np.min(valid_values)
                    except Exception as e:
                        # 计算失败时保持NaN
                        continue
            
            # 写入块结果
            dst.write(chv_block, 1, window=rasterio.windows.Window(0, start_row, width, block_height))
    
    print(f'✓ 完成STMs周期 {period}，统计类型 {stat}，结果保存在: {output_file}')
    return True, output_file

# 主函数
if __name__ == "__main__":
    print(f'CHV时间点并行计算开始时间: {time.strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 处理MTs数据（多个日期并行）
    mt_dates = get_mt_dates()
    if mt_dates:
        print(f"\n=== 处理MTs数据 ===")
        print(f"MTs日期数: {len(mt_dates)}")
        print(f"日期列表: {', '.join(mt_dates)}")
        
        # 使用进程池并行处理多个日期
        with mp.Pool(processes=NUM_PROCESSES) as pool:
            results = list(tqdm(pool.imap(process_single_mt_date, mt_dates), 
                              total=len(mt_dates), desc="处理MTs日期"))
        
        mt_success_count = sum(1 for success, _ in results if success)
        print(f"\nMTs处理完成: {mt_success_count}/{len(results)} 个日期成功")
    
    # 处理STMs数据（多个周期和统计类型组合并行）
    stm_periods = get_stm_periods()
    stm_stats = get_stm_stats()
    
    if stm_periods and stm_stats:
        print(f"\n=== 处理STMs数据 ===")
        print(f"STMs周期数: {len(stm_periods)}")
        print(f"STMs统计类型数: {len(stm_stats)}")
        
        # 创建所有周期和统计类型的组合
        stm_tasks = [(period, stat) for period in stm_periods for stat in stm_stats]
        print(f"总任务数: {len(stm_tasks)}")
        
        # 使用进程池并行处理多个周期和统计类型组合
        with mp.Pool(processes=NUM_PROCESSES) as pool:
            results = list(tqdm(pool.starmap(process_single_stm_period, stm_tasks), 
                              total=len(stm_tasks), desc="处理STMs任务"))
        
        stm_success_count = sum(1 for success, _ in results if success)
        print(f"\nSTMs处理完成: {stm_success_count}/{len(results)} 个任务成功")
    
    print(f'\nCHV计算完成时间: {time.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f"\n所有结果保存在: {OUTPUT_PATH}")
