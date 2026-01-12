import os
import numpy as np
import rasterio
import glob
from collections import defaultdict

def analyze_stm_extremes():
    """分析STM原始数据中1000以上值的分布"""
    print("=== STM原始数据1000以上值分析 ===")
    
    INPUT_PATH = r'D:\背景值处理_2m'
    STM_PATH = os.path.join(INPUT_PATH, 'STMs')
    
    # 获取所有周期
    periods = [d for d in os.listdir(STM_PATH) if os.path.isdir(os.path.join(STM_PATH, d))]
    print(f"\n找到的STM周期: {periods}")
    
    # 分析不同统计类型
    stats = ['maximum', 'mean', 'median', 'minimum', 'range', 'std']
    
    # 结果统计
    all_stats = defaultdict(list)
    total_stats = {
        'files_analyzed': 0,
        'files_with_extremes': 0,
        'total_extreme_pixels': 0,
        'total_pixels': 0
    }
    
    for period in periods:
        print(f"\n=== 分析周期: {period} ===")
        period_path = os.path.join(STM_PATH, period)
        
        # 获取所有指标
        indices = [d for d in os.listdir(period_path) if os.path.isdir(os.path.join(period_path, d))]
        if not indices:
            print("✗ 未找到指标")
            continue
            
        # 选择前3个指标进行分析
        sample_indices = indices[:3]
        print(f"分析指标: {sample_indices}")
        
        for idx in sample_indices:
            idx_path = os.path.join(period_path, idx)
            
            for stat in stats:
                # 查找对应的文件
                files = glob.glob(os.path.join(idx_path, f'*{stat}*.tif'))
                if not files:
                    continue
                    
                file_path = files[0]
                filename = os.path.basename(file_path)
                total_stats['files_analyzed'] += 1
                
                print(f"\n分析文件: {filename}")
                
                try:
                    with rasterio.open(file_path) as src:
                        data = src.read(1)
                        height, width = data.shape
                        total_pixels = height * width
                        
                        # 统计1000以上的值
                        extreme_pixels = np.sum(data > 1000)
                        extreme_ratio = extreme_pixels / total_pixels * 100
                        
                        # 统计2000以上的值
                        very_extreme_pixels = np.sum(data > 2000)
                        very_extreme_ratio = very_extreme_pixels / total_pixels * 100
                        
                        # 统计接近9999的值
                        near_9999 = np.sum((data > 9990) & (data < 10000))
                        
                        print(f"  数据尺寸: {height}x{width} 像素")
                        print(f"  文件nodata值: {src.nodatavals[0]}")
                        print(f"  数据范围: {np.nanmin(data):.2f} - {np.nanmax(data):.2f}")
                        print(f"  >1000像素数: {extreme_pixels} ({extreme_ratio:.3f}%)")
                        print(f"  >2000像素数: {very_extreme_pixels} ({very_extreme_ratio:.3f}%)")
                        print(f"  接近9999像素数: {near_9999}")
                        
                        # 记录统计数据
                        all_stats[stat].append({
                            'filename': filename,
                            'total_pixels': total_pixels,
                            'extreme_pixels': extreme_pixels,
                            'extreme_ratio': extreme_ratio,
                            'very_extreme_pixels': very_extreme_pixels,
                            'very_extreme_ratio': very_extreme_ratio,
                            'near_9999': near_9999,
                            'max_value': np.nanmax(data)
                        })
                        
                        # 更新总体统计
                        total_stats['total_pixels'] += total_pixels
                        total_stats['total_extreme_pixels'] += extreme_pixels
                        
                        if extreme_pixels > 0:
                            total_stats['files_with_extremes'] += 1
                            
                except Exception as e:
                    print(f"  ✗ 分析失败: {e}")
    
    # 汇总分析结果
    print(f"\n=== 汇总分析结果 ===")
    print(f"分析的文件数: {total_stats['files_analyzed']}")
    print(f"包含1000以上值的文件数: {total_stats['files_with_extremes']}")
    print(f"1000以上的总像素数: {total_stats['total_extreme_pixels']}")
    print(f"总像素数: {total_stats['total_pixels']}")
    
    if total_stats['total_pixels'] > 0:
        overall_ratio = total_stats['total_extreme_pixels'] / total_stats['total_pixels'] * 100
        print(f"1000以上值的总体占比: {overall_ratio:.3f}%")
    
    # 按统计类型分析
    print(f"\n=== 按统计类型分析 ===")
    
    for stat in stats:
        stat_files = all_stats.get(stat, [])
        if not stat_files:
            continue
            
        print(f"\n统计类型: {stat}")
        print(f"  分析文件数: {len(stat_files)}")
        
        # 计算平均极端值比例
        avg_extreme_ratio = np.mean([f['extreme_ratio'] for f in stat_files])
        avg_very_extreme_ratio = np.mean([f['very_extreme_ratio'] for f in stat_files])
        
        # 计算最大值
        max_value = np.max([f['max_value'] for f in stat_files])
        
        # 计算包含极端值的文件比例
        files_with_extremes = sum(1 for f in stat_files if f['extreme_pixels'] > 0)
        files_with_extremes_ratio = files_with_extremes / len(stat_files) * 100
        
        print(f"  平均>1000比例: {avg_extreme_ratio:.3f}%")
        print(f"  平均>2000比例: {avg_very_extreme_ratio:.3f}%")
        print(f"  最大值: {max_value:.2f}")
        print(f"  包含极端值的文件比例: {files_with_extremes_ratio:.1f}%")
        
        # 查看最极端的文件
        if stat_files:
            stat_files_sorted = sorted(stat_files, key=lambda x: x['max_value'], reverse=True)
            top_file = stat_files_sorted[0]
            print(f"  极端值最多的文件: {top_file['filename']} (最大值: {top_file['max_value']:.2f}, {top_file['extreme_pixels']}像素)")
    
    # 结论
    print(f"\n=== 结论 ===")
    
    if total_stats['total_extreme_pixels'] == 0:
        print("✓ STM原始数据中没有1000以上的值")
    else:
        extreme_ratio = total_stats['total_extreme_pixels'] / total_stats['total_pixels'] * 100
        print(f"⚠ STM原始数据中存在1000以上的值，占比: {extreme_ratio:.3f}%")
        
        # 确定主要来源
        stat_extreme_ratios = {}
        for stat in stats:
            stat_files = all_stats.get(stat, [])
            if stat_files:
                avg_ratio = np.mean([f['extreme_ratio'] for f in stat_files])
                stat_extreme_ratios[stat] = avg_ratio
        
        if stat_extreme_ratios:
            # 找到极端值最多的统计类型
            max_stat = max(stat_extreme_ratios.items(), key=lambda x: x[1])
            print(f"  极端值主要来自: {max_stat[0]} 统计类型 ({max_stat[1]:.3f}%)")
    
    print(f"\n建议: 根据分析结果调整CHV计算中的极端值过滤阈值")

if __name__ == "__main__":
    analyze_stm_extremes()