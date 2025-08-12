import os
import json
import random
import argparse
from collections import defaultdict

def extract_data(base_dir, output_dir, total_num = 50, seed=42):
    # 设置随机种子（确保结果可重现）
    random.seed(seed)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 定义训练集文件路径
    normal_train_path = os.path.join(base_dir, 'normal', 'train.jsonl')
    hard_train_path = os.path.join(base_dir, 'hard', 'train.jsonl')
    
    # 初始化数据结构：按类别存储题目
    # {category: {'normal': [题目列表], 'hard': [题目列表]}}
    category_data = defaultdict(lambda: {'normal': [], 'hard': []})
    
    # 读取normal训练集数据
    if os.path.exists(normal_train_path):
        with open(normal_train_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line)
                    if 'source' in item:
                        category = item['source']
                        category_data[category]['normal'].append(item)
                except json.JSONDecodeError:
                    print(f"警告：跳过无效JSON行（normal/train.jsonl）")
    else:
        print(f"错误：找不到文件 {normal_train_path}")
        return
    
    # 读取Hard训练集数据
    if os.path.exists(hard_train_path):
        with open(hard_train_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line)
                    if 'source' in item:
                        category = item['source']
                        category_data[category]['hard'].append(item)
                except json.JSONDecodeError:
                    print(f"警告：跳过无效JSON行（hard/train.jsonl）")
    else:
        print(f"错误：找不到文件 {hard_train_path}")
        return
    
    # 准备输出数据结构
    selected_data_normal = []
    selected_data_hard = []
    stats = defaultdict(int)  # 用于统计信息
    
    # 处理每个类别的数据
    for category, data in category_data.items():
        # 获取当前类别的题目列表
        normal_list = data['normal']
        hard_list = data['hard']
        
        # 随机打乱题目顺序
        random.shuffle(normal_list)
        random.shuffle(hard_list)
        
        # 确定hard题目的抽取数量
        hard_count = min(total_num//2, len(hard_list))
        
        # 确定normal题目的抽取数量
        normal_count = min(total_num - hard_count, len(normal_list))
        
        # 记录统计信息
        stats[category] = {
            'normal': len(normal_list),
            'hard': len(hard_list),
            'selected_normal': normal_count,
            'selected_hard': hard_count
        }
        
        # 抽取题目
        if hard_count > 0:
            selected_data_hard.extend(hard_list[:hard_count])
        if normal_count > 0:
            selected_data_normal.extend(normal_list[:normal_count])
    
    # 随机打乱最终选择的题目
    random.shuffle(selected_data_normal)
    random.shuffle(selected_data_hard)
    
    # 输出统计信息
    print("==== 类别统计信息 ====")
    print(f"总类别数: {len(category_data)}")
    print(f"选择的总题目数(normal): {len(selected_data_normal)}")
    print(f"选择的总题目数(hard): {len(selected_data_hard)}")
    print("种子题,原normal题数,原hard题数,选取normal题数,选取hard题数")
    for category, data in category_data.items():
        normal_list = stats[category]["normal"]
        hard_list = stats[category]["hard"]
        normal_count = stats[category]["selected_normal"]
        hard_count = stats[category]["selected_hard"]
        print(category, normal_list, hard_list, normal_count, hard_count)
    print("总normal选取题数：" + str(sum([stats[category]["selected_normal"] for category, data in category_data.items()])))
    print("总hard选取题数：" + str(sum([stats[category]["selected_hard"] for category, data in category_data.items()])))
    
    # 保存选择的题目
    output_path = os.path.join(output_dir, 'train_normal.jsonl')
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in selected_data_normal:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    output_path = os.path.join(output_dir, 'train_hard.jsonl')
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in selected_data_hard:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n选择的题目已保存至: {output_path}")
    print(f"使用随机种子: {seed}")
    print(f"总共选择了 {len(selected_data_normal) + len(selected_data_hard)} 道题目")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='从normal和Hard训练集中按类别抽取题目')
    parser.add_argument('--base_dir', required=True, help='包含normal和hard子目录的基础目录路径')
    parser.add_argument('--output_dir', default='selected_data', help='输出目录路径')
    parser.add_argument('--total', default=50, help='总筛选题数')
    # 添加随机种子参数
    parser.add_argument('--seed', type=int, default=42, help='随机数种子（确保结果可重现）')
    
    args = parser.parse_args()
    
    extract_data(args.base_dir, args.output_dir, seed=args.seed)