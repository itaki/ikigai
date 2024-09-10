# tools/ad_converter_data_collector/batch_plot_generator.py
import os
import pandas as pd
import matplotlib.pyplot as plt
from loguru import logger
import json

# Set up logging
logger.add("batch_plot_generator.log", rotation="10 MB")

def load_parquet_data(file_path):
    return pd.read_parquet(file_path)

def load_metadata(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_plots(data_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    for file in os.listdir(data_dir):
        if file.endswith('.parquet'):
            file_path = os.path.join(data_dir, file)
            base_name = file[:-8]  # Remove '.parquet'
            metadata_file = os.path.join(data_dir, f"{base_name}_metadata.json")
            
            logger.info(f"Processing file: {file}")
            
            try:
                data = load_parquet_data(file_path)
                metadata = load_metadata(metadata_file)
                pin_assignments = metadata.get('pin_assignments', {})
                
                # Remove the first data point
                data = data.iloc[1:]
                
                for column in data.columns:
                    if column != 'timestamp':
                        pin_number = column.split('_')[-1]
                        pin_name = pin_assignments.get(pin_number, f"Pin {pin_number}")
                        
                        plt.figure(figsize=(20, 10))  # Large figure size for big monitors
                        
                        if 'timestamp' in data.columns:
                            plt.plot(data['timestamp'], data[column])
                            plt.xlabel('Timestamp')
                        else:
                            plt.plot(data[column])
                            plt.xlabel('Sample Number')
                        
                        plt.title(f'{base_name} - {pin_name}')
                        plt.ylabel('Voltage')
                        
                        if 'timestamp' in data.columns:
                            plt.xticks(rotation=45, ha='right')
                        
                        plt.tight_layout()
                        
                        # Use pin name in the output filename
                        safe_pin_name = pin_name.replace(" ", "_").replace("/", "_")
                        output_file = os.path.join(output_dir, f"{base_name}_{safe_pin_name}.png")
                        plt.savefig(output_file, dpi=300)
                        plt.close()
                        
                        logger.info(f"Generated plot: {output_file}")
            
            except Exception as e:
                logger.error(f"Error processing {file}: {str(e)}")

if __name__ == "__main__":
    data_dir = 'tools/ad_converter_data_collector/test_data'
    output_dir = 'tools/ad_converter_data_collector/output_plots'
    
    generate_plots(data_dir, output_dir)
    logger.info("Batch plot generation completed.")
