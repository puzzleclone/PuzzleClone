import os
import json
import random
from pathlib import Path
from collections import defaultdict

def split_dataset(input_dir, output_dir, difficulty_threshold=0.5, train_percentage=0.8, validate_percentage=0.1, seed=42):
    # 设置随机种子（确保结果可重现）
    random.seed(seed)
    
    # 初始化存储数据结构
    # source_type -> difficulty_level -> [items]
    source_data = defaultdict(lambda: defaultdict(list))
    
    # 遍历输入目录中的所有JSONL文件
    for file_name in os.listdir(input_dir):
        if file_name.endswith('.jsonl'):
            file_path = os.path.join(input_dir, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        item = json.loads(line.strip())
                        difficulty = item.get('difficulty', 0)
                        source_type = item.get('source', "default")
                        
                        # 根据难度分类
                        difficulty_level = 'hard' if difficulty > difficulty_threshold else 'normal'
                        source_data[source_type][difficulty_level].append(item)
                    except json.JSONDecodeError:
                        print(f"警告：跳过无效JSON行（文件：{file_name}）")
    
    # 创建输出目录结构
    output_paths = {
        'normal': {
            'train': os.path.join(output_dir, 'normal', 'train.jsonl'),
            'train_rl': os.path.join(output_dir, 'normal', 'train_rl.jsonl'),
            'validate': os.path.join(output_dir, 'normal', 'validate.jsonl'),
            'test': os.path.join(output_dir, 'normal', 'test.jsonl')
        },
        'hard': {
            'train': os.path.join(output_dir, 'hard', 'train.jsonl'),
            'train_rl': os.path.join(output_dir, 'hard', 'train_rl.jsonl'),
            'validate': os.path.join(output_dir, 'hard', 'validate.jsonl'),
            'test': os.path.join(output_dir, 'hard', 'test.jsonl')
        }
    }
    
    # 确保输出目录存在
    for category in ['normal', 'hard']:
        Path(output_paths[category]['train']).parent.mkdir(parents=True, exist_ok=True)
    
    # 初始化最终合并的数据集
    merged_data = {
        'normal': defaultdict(list),
        'hard': defaultdict(list)
    }
    
    # 处理每个来源类型
    for source_type, difficulty_groups in source_data.items():
        for difficulty_level, items in difficulty_groups.items():
            if not items:
                continue
                
            # 随机打乱当前组数据
            random.shuffle(items)
            
            # 计算分割点
            validate_index = int((train_percentage + validate_percentage) * len(items))
            train_rl_index = validate_index - 5
            
            # 获取各个子集
            train_rl_items = items[:train_rl_index]
            validate_items = items[train_rl_index:validate_index]
            train_items = items[:validate_index]  # 整个训练部分（包括RL训练和验证）
            test_items = items[validate_index:]
            
            # 添加到合并数据集
            merged_data[difficulty_level]['train_rl'].extend(train_rl_items)
            merged_data[difficulty_level]['train'].extend(train_items)
            merged_data[difficulty_level]['validate'].extend(validate_items)
            merged_data[difficulty_level]['test'].extend(test_items)
    
    # 写入最终合并的文件
    for difficulty_level, data_groups in merged_data.items():
        # 写入训练集
        with open(output_paths[difficulty_level]['train'], 'w', encoding='utf-8') as f:
            for item in data_groups['train']:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        # 写入强化训练训练集
        with open(output_paths[difficulty_level]['train_rl'], 'w', encoding='utf-8') as f:
            for item in data_groups['train_rl']:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        # 写入验证集
        with open(output_paths[difficulty_level]['validate'], 'w', encoding='utf-8') as f:
            for item in data_groups['validate']:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        # 写入测试集
        with open(output_paths[difficulty_level]['test'], 'w', encoding='utf-8') as f:
            for item in data_groups['test']:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"处理完成！结果保存在: {output_dir}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='根据题目类型和难度划分数据集')
    parser.add_argument('-i', '--input', type=str, required=True, help='输入JSONL文件目录')
    parser.add_argument('-o', '--output', type=str, default='output', help='输出目录')
    parser.add_argument('--seed', type=int, default=42, required=False, help='随机数种子（确保结果可重现）')
    
    args = parser.parse_args()
    
    split_dataset(args.input, args.output, seed=args.seed)