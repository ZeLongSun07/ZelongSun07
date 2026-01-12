import os
import numpy as np
import rasterio

# 检查空间分布一致性的函数
def check_spatial_consistency(original_file, chv_file):
    print(f"\n=== 检查空间分布一致性 ===")
    print(f"原始文件: {os.path.basename(original_file)}")
    print(f"CHV文件: {os.path.basename(chv_file)}")
    
    # 读取原始文件
    try:
        with rasterio.open(original_file) as src_original:
            data_original = src_original.read(1)
            height, width = src_original.shape
            
            # 获取原始文件的有效像素掩码
            original_mask = ~np.isnan(data_original)
            original_valid_count = np.sum(original_mask)
            
            print(f"\n原始文件统计:")
            print(f"  尺寸: {height}x{width}")
            print(f"  总像素数: {height * width}")
            print(f"  有效像素数: {original_valid_count}")
            print(f"  有效像素比例: {original_valid_count / (height * width) * 100:.2f}%")
            
            # 读取CHV文件
            with rasterio.open(chv_file) as src_chv:
                data_chv = src_chv.read(1)
                
                # 检查尺寸是否一致
                if src_chv.shape != (height, width):
                    print(f"  错误: 文件尺寸不一致! CHV尺寸: {src_chv.shape}")
                    return False
                
                # 获取CHV文件的有效像素掩码
                chv_mask = ~np.isnan(data_chv)
                chv_valid_count = np.sum(chv_mask)
                
                print(f"\nCHV文件统计:")
                print(f"  尺寸: {src_chv.shape[0]}x{src_chv.shape[1]}")
                print(f"  总像素数: {src_chv.shape[0] * src_chv.shape[1]}")
                print(f"  有效像素数: {chv_valid_count}")
                print(f"  有效像素比例: {chv_valid_count / (src_chv.shape[0] * src_chv.shape[1]) * 100:.2f}%")
                
                # 比较空间分布
                print(f"\n空间分布比较:")
                
                # 原始有值但CHV无值的像素
                original_only = original_mask & ~chv_mask
                original_only_count = np.sum(original_only)
                
                # CHV有值但原始无值的像素
                chv_only = ~original_mask & chv_mask
                chv_only_count = np.sum(chv_only)
                
                # 两者都有值的像素
                both_valid = original_mask & chv_mask
                both_valid_count = np.sum(both_valid)
                
                print(f"  原始有值但CHV无值的像素数: {original_only_count}")
                print(f"  原始有值但CHV无值的像素比例: {original_only_count / original_valid_count * 100:.2f}%")
                
                print(f"  CHV有值但原始无值的像素数: {chv_only_count}")
                print(f"  CHV有值但原始无值的像素比例: {chv_only_count / chv_valid_count * 100:.2f}%")
                
                print(f"  两者都有值的像素数: {both_valid_count}")
                print(f"  两者都有值的像素比例: {both_valid_count / original_valid_count * 100:.2f}%")
                
                # 检查是否有空间分布差异
                if original_only_count == 0 and chv_only_count == 0:
                    print(f"\n✓ 空间分布完全一致!")
                    return True
                else:
                    print(f"\n⚠ 空间分布存在差异!")
                    
                    # 显示差异的大致位置
                    if original_only_count > 0:
                        original_only_coords = np.where(original_only)
                        print(f"  原始有值但CHV无值的像素分布示例:")
                        print(f"    行数范围: {original_only_coords[0].min()} ~ {original_only_coords[0].max()}")
                        print(f"    列数范围: {original_only_coords[1].min()} ~ {original_only_coords[1].max()}")
                    
                    if chv_only_count > 0:
                        chv_only_coords = np.where(chv_only)
                        print(f"  CHV有值但原始无值的像素分布示例:")
                        print(f"    行数范围: {chv_only_coords[0].min()} ~ {chv_only_coords[0].max()}")
                        print(f"    列数范围: {chv_only_coords[1].min()} ~ {chv_only_coords[1].max()}")
                    
                    return False
                    
    except Exception as e:
        print(f"  错误: {str(e)}")
        return False

# 主函数
def main():
    # 检查几个示例文件
    mt_files = [
        '0510', '0519', '0612', '0626', '0711', '0723', '0812', '0826'
    ]
    
    for date in mt_files[:3]:  # 只检查前3个文件
        original_file = os.path.join(r'D:\背景值处理_2m\MTs\ARI', f'{date}_ARI.tif')
        chv_file = os.path.join(r'D:\背景值处理_2m\CHV_2m', f'CHV_MTs_{date}.tif')
        
        if os.path.exists(original_file) and os.path.exists(chv_file):
            check_spatial_consistency(original_file, chv_file)
        else:
            print(f"\n跳过文件: 原始文件或CHV文件不存在")
            print(f"  原始文件: {original_file}")
            print(f"  CHV文件: {chv_file}")

if __name__ == '__main__':
    main()
