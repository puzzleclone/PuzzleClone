#!/bin/bash
# 添加域
# python data_format.py -i puzzle_clone_public_7_29/data -o puzzle_clone_public_7_29/data_formatted -d puzzle_clone_public_7_29/specs-mark --add-ids
# 计算难度
python cal_difficulty.py difficulty -i puzzle_clone_public_7_29/data_formatted -o puzzle_clone_public_7_29/data_with_difficulty
# 计算难度分布
python cal_difficulty.py distribution -i puzzle_clone_public_7_29/data_with_difficulty -o reports_7_29/difficulty_distribution/difficulty_distribution_ori.json
# 检查重复
python check_duplicate.py detail -i puzzle_clone_public_7_29/data_with_difficulty -o reports_7_29/check_duplicate/duplicate_detail.txt
# 生成重复数据的汇总报告
python check_duplicate.py overview -i puzzle_clone_public_7_29/data_with_difficulty -o reports_7_29/check_duplicate/duplicate_overview.csv
# 可视化去重结果
python visualize_duplicate.py -i reports_7_29/check_duplicate/duplicate_overview.csv -o reports_7_29/check_duplicate/duplicate_report.png
# 可视化去重结果
python visualize_duplicate.py -i reports_7_29/check_duplicate/duplicate_overview.csv -o reports_7_29/check_duplicate/duplicate_report_hide_zero.png --hide-zero
# 去重
python deduplicate.py -i puzzle_clone_public_7_29/data_with_difficulty -o puzzle_clone_public_7_29/deduplicated_data
# 计算去重后数据的难度分布
python cal_difficulty.py distribution -i puzzle_clone_public_7_29/deduplicated_data -o reports_7_29/difficulty_distribution/difficulty_distribution_deduplicated.json
# 可视化难度（算全部题，折线+柱状图）
python visualize_difficulty_all.py -a reports_7_29/difficulty_distribution/difficulty_distribution_ori.json -b reports_7_29/difficulty_distribution/difficulty_distribution_deduplicated.json -o reports_7_29/difficulty_distribution/difficulty_distribution_report_all.png
# 可视化难度（算每个题）
python visualize_difficulty.py -i puzzle_clone_public_7_29/deduplicated_data -o reports_7_29/difficulty_distribution/difficulty_distribution_report.png
# 切分
python split_rl.py -i puzzle_clone_public_7_29/deduplicated_data -o puzzle_clone_public_7_29/splitted
# SFT
python gen_sft_data.py --base_dir puzzle_clone_public_7_29/splitted --output_dir puzzle_clone_public_7_29/data_sft