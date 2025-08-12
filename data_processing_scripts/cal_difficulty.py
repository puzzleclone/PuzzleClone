import json
import os
import argparse
from typing import Dict, Tuple

def sort_dict_by_key(data: Dict, granularity: bool = False, switch_to_key_value: bool = True) -> Dict:
    """
    Sort and merge dictionary data for difficulty distribution analysis.
    
    This function processes difficulty distribution data by either maintaining fine-grained
    scores or merging them into 10 intervals for better visualization.
    
    Args:
        data: Dictionary containing difficulty scores as keys and counts as values
        granularity: If True, maintains fine-grained scores; if False, merges into intervals
        switch_to_key_value: If True, sorts by keys; if False, sorts by values
        
    Returns:
        Processed dictionary with sorted/merged difficulty distribution
    """
    if granularity:
        if switch_to_key_value:
            # 按键排序（转换为浮点数后降序）
            sorted_items = sorted(data.items(), key=lambda item: float(item[0]), reverse=True)
            return dict(sorted_items)
        else:
            # 按值排序（降序）
            sorted_items = sorted(data.items(), key=lambda item: item[1], reverse=True)
            return dict(sorted_items)
    else:
        sorted_items = sorted(data.items(), key=lambda item: item[1], reverse=True)
        
        float_keys = [float(key) for key, _ in sorted_items]
        
        min_key = min(float_keys)
        max_key = max(float_keys)
        interval_width = (max_key - min_key) / 10
        
        merged_dict = {}
        for i in range(10):
            start = min_key + i * interval_width
            end = start + interval_width
            interval_key = f"({start:.2f}, {end:.2f}]" if i > 0 else f"[{start:.2f}, {end:.2f}]"
            merged_dict[interval_key] = 0
        
        for key_str, value in sorted_items:
            key_float = float(key_str)
            # 找到对应的区间索引
            index = 9
            for t in range(9, -1, -1):
                if key_float <= min_key + interval_width * (t + 1):
                    index = t
            
            # 找到对应的区间键
            start = min_key + index * interval_width
            end = start + interval_width
            interval_key = f"({start:.2f}, {end:.2f}]" if index > 0 else f"[{start:.2f}, {end:.2f}]"
            merged_dict[interval_key] += value
    
    return merged_dict

def min_max_score(list_jsonl: list) -> Tuple[Tuple, Tuple, Tuple]:
    """
    计算problem长度、cond_num和sym_num的最小最大值
    
    Args:
        list_jsonl: JSONL文件内容列表
        
    Returns:
        (len_min_max, cond_min_max, sym_min_max)
    """
    list_len = []
    list_cond = []
    list_sym = []
    for line in list_jsonl:
        temp = json.loads(line)
        list_len.append(len(temp["problem"]))
        list_cond.append(temp["parameters"]["cond_num"])
        list_sym.append(temp["parameters"]["sym_num"])
    len_min_max = (min(list_len), max(list_len))
    cond_min_max = (min(list_cond), max(list_cond))
    sym_min_max = (min(list_sym), max(list_sym))
    return (len_min_max, cond_min_max, sym_min_max)

def norm_num(data: Dict, len_min_max: Tuple, cond_min_max: Tuple, sym_min_max: Tuple) -> float:
    """
    计算归一化难度分数
    
    Args:
        data: 单条数据记录
        len_min_max: problem长度的最小最大值
        cond_min_max: cond_num的最小最大值
        sym_min_max: sym_num的最小最大值
        
    Returns:
        归一化后的难度分数
    """
    if len_min_max[0] == len_min_max[1]:
        len_norm = 0.5
    else:
        len_norm = (len(data["problem"])-len_min_max[0])/(len_min_max[1]-len_min_max[0])
    if cond_min_max[0] == cond_min_max[1]:
        cond_norm = 0.5
    else:
        cond_norm = (data["parameters"]["cond_num"]-cond_min_max[0])/(cond_min_max[1]-cond_min_max[0])
    if sym_min_max[0] == sym_min_max[1]:
        sym_norm = 0.5
    else:
        sym_norm = (data["parameters"]["sym_num"]-sym_min_max[0])/(sym_min_max[1]-sym_min_max[0])
    return round((len_norm+cond_norm+sym_norm+data["parameters"]["vars_scale"])/4, 3)

def generate_difficulty(data_path: str, output_path: str) -> None:
    """
    生成难度分数并写入文件
    
    Args:
        data_path: 输入数据目录
        output_path: 输出目录
    """
    os.makedirs(output_path, exist_ok=True)
    
    for dir_add, _, file_list in os.walk(data_path):
        for file in file_list:
            if not file.endswith('.jsonl'):
                continue
                
            print(f"Processing {file}")
            input_file = os.path.join(dir_add, file)
            output_file = os.path.join(output_path, file)
            
            with open(input_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                len_min_max, cond_min_max, sym_min_max = min_max_score(lines)
                
                output_lines = []
                for line in lines:
                    data = json.loads(line)
                    difficulty_score = norm_num(data, len_min_max, cond_min_max, sym_min_max)
                    data["difficulty"] = difficulty_score
                    output_lines.append(json.dumps(data, ensure_ascii=False) + '\n')
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.writelines(output_lines)

def generate_distribution(data_path: str, output_file: str, granularity: bool = False, switch_to_key: bool = False) -> None:
    """
    生成难度分布统计
    
    Args:
        data_path: 输入数据目录
        output_file: 输出文件路径
        granularity: 是否保持细粒度
        switch_to_key: 是否按键排序
    """
    dict_sum = {}
    dict_sum_sorted = {}
    
    for dir_add, _, file_list in os.walk(data_path):
        for file in file_list:
            if not file.endswith('.jsonl'):
                continue
                
            print(f"Processing {file}")
            input_file = os.path.join(dir_add, file)
            
            with open(input_file, "r", encoding="utf-8") as f:
                dict_single = {}
                lines = f.readlines()
                len_min_max, cond_min_max, sym_min_max = min_max_score(lines)
                
                for line in lines:
                    data = json.loads(line)
                    difficulty_score = norm_num(data, len_min_max, cond_min_max, sym_min_max)
                    key = str(difficulty_score)
                    dict_single[key] = dict_single.get(key, 0) + 1
                
            sorted_dict_single = sort_dict_by_key(dict_single, granularity=granularity, switch_to_key_value=switch_to_key)
            dict_sum[file] = dict_single
            dict_sum_sorted[file] = sorted_dict_single
    
    # 计算所有文件的汇总统计
    all_sum = {}
    for key, sub_dict in dict_sum.items():
        if key != "all":
            for k, v in sub_dict.items():
                all_sum[k] = all_sum.get(k, 0) + v
    dict_sum["all"] = all_sum
    dict_sum_sorted["all"] = sort_dict_by_key(all_sum, granularity=granularity, switch_to_key_value=switch_to_key)
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dict_sum_sorted, f, ensure_ascii=False, indent=4)

def main():
    parser = argparse.ArgumentParser(description='处理JSONL文件生成难度分数或分布统计')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # difficulty 子命令
    difficulty_parser = subparsers.add_parser('difficulty', help='生成难度分数')
    difficulty_parser.add_argument('-i', '--input', required=True, help='输入数据目录')
    difficulty_parser.add_argument('-o', '--output', required=True, help='输出目录')
    
    # distribution 子命令
    distribution_parser = subparsers.add_parser('distribution', help='生成难度分布统计')
    distribution_parser.add_argument('-i', '--input', required=True, help='输入数据目录')
    distribution_parser.add_argument('-o', '--output', required=True, help='输出文件路径')
    distribution_parser.add_argument('--granularity', action='store_true', help='保持细粒度（不合并区间）')
    distribution_parser.add_argument('--sort-by-key', action='store_true', help='按键排序（默认按值排序）')
    
    args = parser.parse_args()
    
    if args.command == 'difficulty':
        print("开始生成难度分数...")
        generate_difficulty(args.input, args.output)
        print("难度分数生成完成！")
    elif args.command == 'distribution':
        print("开始生成难度分布统计...")
        generate_distribution(
            args.input, 
            args.output, 
            granularity=args.granularity, 
            switch_to_key=args.sort_by_key
        )
        print("难度分布统计生成完成！")

if __name__ == "__main__":
    main()