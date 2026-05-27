import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def main():
    # CSV 파일 경로 설정
    csv_path = 'result/uwb_a_result.csv'
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} 파일을 찾을 수 없습니다. 경로를 확인해 주세요.")
        return

    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path)

    # 빈 행이나 필수 값이 누락된 행 정제
    df = df.dropna(subset=['real_target_azimuth', 'error'])

    # real_target_azimuth 값에 따른 error의 평균 구하기
    df_grouped = df.groupby('real_target_azimuth')['error'].mean().reset_index()

    # X축(각도) 기준 오름차순 정렬 (순서대로 꺾은선이 그려지도록 설정)
    df_grouped = df_grouped.sort_values(by='real_target_azimuth')

    print("\n--- [각도별 평균 에러 데이터] ---")
    print(df_grouped.to_string(index=False))

    # 그래프 스타일 설정 (Seaborn 테마 적용)
    sns.set_theme(style="whitegrid")
    
    # 폰트 깨짐 방지 설정 (기본 맑은 고딕 사용 및 마이너스 기호 깨짐 방지)
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False

    plt.figure(figsize=(10, 6))

    # 1안: 마커가 포함된 꺾은선 그래프 그리기
    plt.plot(
        df_grouped['real_target_azimuth'], 
        df_grouped['error'], 
        marker='o', 
        linestyle='-', 
        linewidth=2, 
        markersize=6, 
        color='#1f77b4', 
        label='평균 에러 (Average Error)'
    )

    # 그래프 장식 설정
    plt.title('Real Target Azimuth vs Average Error (1안: 꺾은선 그래프)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Real Target Azimuth (degrees)', fontsize=12, labelpad=10)
    plt.ylabel('Average Error (degrees)', fontsize=12, labelpad=10)
    plt.axhline(0, color='gray', linestyle='--', linewidth=0.8) # 0 기준선 추가
    plt.legend(loc='best')
    plt.tight_layout()

    # 이미지 저장 경로 설정 및 폴더 생성 확인
    output_dir = 'result'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, 'uwb_error_line_chart.png')
    plt.savefig(output_path, dpi=300)
    print(f"\n[성공] 꺾은선 그래프가 저장되었습니다: {output_path}")

    # 그래프 화면 출력
    plt.show()

if __name__ == '__main__':
    main()
