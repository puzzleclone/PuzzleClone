import json
import os
from typing import Dict, Any, List, Tuple
import argparse

def process_jsonl_files(input_dir: str, output_dir: str, dsl_dir: str = None, add_ids: bool = False) -> None:
    """
    Process all JSONL files in a directory, adding metadata fields and calculating scale parameters.
    
    This function formats raw puzzle data by:
    1. Adding question type (qtype) and evaluation type (eval_type) metadata
    2. Calculating normalized variable scale (vars_scale) from DSL specifications
    3. Adding unique IDs if requested
    4. Adding source field based on filename
    
    Args:
        input_dir: Input directory containing raw JSONL files
        output_dir: Output directory for formatted JSONL files
        dsl_dir: DSL specification directory (optional, used for vars_scale calculation)
        add_ids: Whether to add unique ID fields (format: filename-linenumber)
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Process all files in the input directory
    for filename in os.listdir(input_dir):
        if not filename.endswith('.jsonl'):
            continue
            
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        # Extract filename (without extension) to use as source value
        source_value = os.path.splitext(filename)[0]
        
        print(f"\nProcessing file: {filename}")
        
        qtype_value = ''
        eval_type_value = ''
        # Read first record as reference for metadata
        with open(input_path, 'r', encoding='utf-8') as infile:
            first_line = infile.readline()
            try:
                first_record = json.loads(first_line)
                if 'qtype' in first_record and 'eval_type' in first_record:
                    # Validate existing qtype values
                    for qi in first_record['qtype'].split(','):
                        if qi not in ["简答题", "单选题", "填空题"]:
                            print(f"File qtype validation error: {qi} is invalid, qtype is {first_record['qtype']}")
                            return
                    # Validate existing eval_type values
                    for ei in first_record['eval_type'].split(','):
                        if ei not in ["nominal", "numeral", "option", "ordered array", "unordered array"] and len(ei) != 11:
                            print(f"File eval_type validation error: {ei}, eval_type is {first_record['eval_type']}")
                            return
                    print("File already contains qtype and eval_type fields, skipping addition")
                    qtype_value = first_record['qtype']
                    eval_type_value = first_record['eval_type']
            except json.JSONDecodeError:
                print("Unable to parse first record as example")
                first_record = {}
        
        if qtype_value == '' or eval_type_value == '':
            # Get user input for qtype and eval_type for current file
            print("\nExample record for reference:")
            print(first_record.get("problem", ""), first_record.get("answer", ""))
            qtype_value = input("\nPlease enter qtype value for this file: ")
            eval_type_value = input("Please enter eval_type value for this file: ")
        
        print(f"\nStarting processing {input_path} -> {output_path}")
        
        # Read all data from input file
        all_data: List[Dict[str, Any]] = []
        with open(input_path, 'r', encoding='utf-8') as infile:
            for line_number, line in enumerate(infile, 1):
                try:
                    record = json.loads(line)
                    
                    # Add unique ID if requested
                    if add_ids and 'id' not in record:
                        line_num_str = f"{line_number:04d}"
                        record['id'] = f"{source_value}-{line_num_str}"
                    
                    all_data.append(record)
                except json.JSONDecodeError as e:
                    print(f"Parse error (line {line_number}, content: {line.strip()}): {e}")
                    continue
        
        # Calculate vars_scale if DSL directory is provided
        if dsl_dir:
            # Get DSL file path
            dsl_file_name = source_value + '.json'
            dsl_file_path = os.path.join(dsl_dir, dsl_file_name)
            
            # Parse DSL file to get variables that need normalization
            vars = []
            diff_factors = []
            try:
                with open(dsl_file_path, 'r', encoding='utf-8') as f:
                    dsl = json.load(f)
                    if "defined_vars" in dsl:
                        for k, v in dsl["defined_vars"].items():
                            if "domain" in v:
                                vars.append(k)
                                diff_factors.append(v["diff_factor"] if "diff_factor" in v else 0)
                print(f"Variables requiring normalization: {vars}")
            except Exception as e:
                print(f"Error reading DSL file {dsl_file_path}: {e}")
                vars = []
            
            # Calculate min and max values for each variable
            var_min_max: Dict[str, Tuple[float, float]] = {}
            for var in vars:
                values: List[float] = []
                for data in all_data:
                    if "config" in data and var in data["config"]:
                        value = data["config"][var]
                        if isinstance(value, (int, float)):
                            values.append(float(value))
                
                if values:
                    min_val = min(values)
                    max_val = max(values)
                    var_min_max[var] = (min_val, max_val)
                    print(f"Variable {var} value range: [{min_val}, {max_val}]")
            
            # Calculate vars_scale and add to each record
            for data in all_data:
                normalized_values = []
                config = data.get("config", {})
                
                # Process each variable with its difficulty factor
                for var, diff in zip(vars, diff_factors):
                    if var in config and var in var_min_max:
                        value = config[var]
                        
                        if isinstance(value, (int, float)):
                            min_val, max_val = var_min_max[var]
                            value_range = max_val - min_val
                            
                            # Normalize value to [0, 1] range
                            if value_range > 0:
                                normalized = (value - min_val) / value_range
                            else:
                                normalized = 0.5  # Default for constant values
                            
                            # Adjust based on difficulty factor
                            if diff > 0:
                                normalized_values.append(normalized)
                            elif diff < 0:
                                normalized_values.append(1 - normalized)  # Invert for negative difficulty
                
                # Calculate average normalized scale
                if normalized_values:
                    avg_scale = sum(normalized_values) / len(normalized_values)
                else:
                    avg_scale = 0.5  # Default when no variables to normalize
                
                # Add vars_scale parameter to record
                if "parameters" not in data:
                    data["parameters"] = {}
                data["parameters"]["vars_scale"] = avg_scale
        
        # Add metadata fields to all records
        for record in all_data:
            if qtype_value:
                record["qtype"] = qtype_value
            if eval_type_value:
                record["eval_type"] = eval_type_value
            record["source"] = source_value
        
        # Write processed data to output file
        with open(output_path, 'w', encoding='utf-8') as outfile:
            for record in all_data:
                outfile.write(json.dumps(record, ensure_ascii=False) + '\n')

def main():
    """Main entry point for the data formatting tool."""
    parser = argparse.ArgumentParser(description='Format and preprocess JSONL puzzle files with metadata and variable scaling')
    parser.add_argument('-i', '--input', default='tmp', help='Input directory path (default: "tmp")')
    parser.add_argument('-o', '--output', default='.', help='Output directory path (default: current directory)')
    parser.add_argument('-d', '--dsl', help='DSL specification directory path (used for vars_scale calculation)')
    parser.add_argument('--add-ids', action='store_true', help='Add unique ID fields (format: filename-linenumber)')
    
    args = parser.parse_args()
    
    print("Starting JSONL file processing...")
    process_jsonl_files(args.input, args.output, args.dsl, args.add_ids)
    print("\nAll files processed successfully!")

if __name__ == "__main__":
    main()