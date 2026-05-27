import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def main():
    # CSV file path
    csv_path = 'result/uwb_a_result.csv'
    
    if not os.path.exists(csv_path):
        print(f"Error: Could not find {csv_path}. Please check the path.")
        return

    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path)

    # Clean empty/summary rows
    df = df.dropna(subset=['real_target_azimuth', 'align_recog_time_ms'])
    df = df.reset_index(drop=True)
    
    total_data_count = len(df)
    print(f"Total valid data rows in CSV: {total_data_count}")

    # Exclude the first row of each of the 3 blocks (indices 0, 22, 44)
    # 66 - 3 = 63 data points
    exclude_indices = [0, 22, 44]
    df_filtered = df.drop(exclude_indices).reset_index(drop=True)
    
    filtered_data_count = len(df_filtered)
    print(f"Filtered data rows (excluding initial test runs): {filtered_data_count}")

    # Calculate overall average alignment time from the 63 data points
    overall_avg_time = df_filtered['align_recog_time_ms'].mean()
    print(f"Calculated Overall Average Alignment Time: {overall_avg_time:.2f} ms")

    # Group by real_target_azimuth and compute the mean alignment time for each angle
    df_grouped = df_filtered.groupby('real_target_azimuth')['align_recog_time_ms'].mean().reset_index()
    df_grouped = df_grouped.sort_values(by='real_target_azimuth')

    print("\n--- [Averaged Alignment Time per Azimuth Angle (63 points)] ---")
    print(df_grouped.to_string(index=False))

    # Set Seaborn theme for academic papers
    sns.set_theme(style="ticks")
    
    # Configure font and prevent unicode minus sign issues
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    plt.figure(figsize=(10, 6))

    # Plot the line chart with markers
    plt.plot(
        df_grouped['real_target_azimuth'], 
        df_grouped['align_recog_time_ms'], 
        marker='o', 
        linestyle='-', 
        linewidth=3, 
        markersize=8, 
        color='#1f77b4', 
        label='Alignment Time'
    )

    # Plot the horizontal line for the overall Average Alignment Time
    plt.axhline(
        overall_avg_time, 
        color='red', 
        linestyle='--', 
        linewidth=2, 
        label=f'Average Alignment Time ({overall_avg_time:.2f} ms)'
    )

    # Academic-style chart annotations (English only)
    # plt.title('Alignment Time', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('Real Target Azimuth (degrees)', fontsize=24, labelpad=15)
    plt.ylabel('Alignment Time (ms)', fontsize=24, labelpad=15)
    
    # Configure X-axis ticks in steps of 10, from -50 to 50
    x_ticks = [-50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50]
    plt.xticks(ticks=x_ticks, fontsize=20)
    plt.yticks(fontsize=20)
    plt.xlim(-55, 55)
    plt.ylim(0, max(df_grouped['align_recog_time_ms'].max() + 100, overall_avg_time + 100))
    
    # Add minor grid lines
    plt.grid(True, which='both', linestyle=':', alpha=0.5)
    
    plt.legend(loc='best', fontsize=20, frameon=True)
    plt.tight_layout()

    # Save to the result directory
    output_dir = 'result'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, 'uwb_alignment_time_chart.png')
    plt.savefig(output_path, dpi=300)
    print(f"\n[Success] Alignment time chart saved: {output_path}")

    # Display plot
    plt.show()

if __name__ == '__main__':
    main()
