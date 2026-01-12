import os
import numpy as np
import rasterio

# 检查原始MTs数据
mt_path = r'D:\背景值处理_2m\MTs\ARI\0510_ARI.tif'
print(f"检查原始数据文件: {mt_path}")

if os.path.exists(mt_path):
    try:
        with rasterio.open(mt_path) as src:
            # 获取基本信息
            height, width = src.shape
            count = src.count
            dtype = src.dtypes[0]
            nodata = src.nodatavals[0]
            
            print(f"  尺寸: {height}x{width}")
            print(f"  波段数: {count}")
            print(f"  数据类型: {dtype}")
            print(f"  NoData值: {nodata}")
            
            # 读取数据
            data = src.read(1)
            
            # 计算统计信息
            valid_data = data[~np.isnan(data)]
            
            if len(valid_data) == 0:
                print("  警告: 没有有效数据")
            else:
                # 基本统计
                min_val = np.min(valid_data)
                max_val = np.max(valid_data)
                mean_val = np.mean(valid_data)
                std_val = np.std(valid_data)
                
                print(f"  有效像素数: {len(valid_data)}")
                print(f"  最小值: {min_val:.4f}")
                print(f"  最大值: {max_val:.4f}")
                print(f"  平均值: {mean_val:.4f}")
                print(f"  标准差: {std_val:.4f}")
                print(f"  数据范围: [{min_val:.2f}, {max_val:.2f}]")
                
    except Exception as e:
        print(f"  错误: {str(e)}")
else:
    print(f"  文件不存在: {mt_path}")
    print("  检查目录结构:")
    mt_dir = os.path.dirname(mt_path)
    if os.path.exists(mt_dir):
        files = os.listdir(mt_dir)
        print(f"  目录 {mt_dir} 中的文件:")
        for f in files[:5]:
            print(f"    {f}")
        if len(files) > 5:
            print(f"    ... 共 {len(files)} 个文件")