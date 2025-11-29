"""
matplotlib日本語フォント設定ユーティリティ

Windows環境でmatplotlibの日本語表示を有効化
"""

import matplotlib.pyplot as plt
import matplotlib
import platform


def setup_japanese_font():
    """
    matplotlibで日本語を表示できるように設定
    
    Windows環境でのフォント設定を自動的に行う
    """
    system = platform.system()
    
    if system == 'Windows':
        # Windowsの場合
        try:
            # MS Gothic (游ゴシック) を試す
            plt.rcParams['font.family'] = 'MS Gothic'
        except:
            try:
                # Yu Gothic を試す
                plt.rcParams['font.family'] = 'Yu Gothic'
            except:
                try:
                    # Meiryo を試す
                    plt.rcParams['font.family'] = 'Meiryo'
                except:
                    print("Warning: Could not set Japanese font. Japanese text may not display correctly.")
    
    elif system == 'Darwin':  # macOS
        plt.rcParams['font.family'] = 'Hiragino Sans'
    
    elif system == 'Linux':
        try:
            plt.rcParams['font.family'] = 'Noto Sans CJK JP'
        except:
            try:
                plt.rcParams['font.family'] = 'IPAGothic'
            except:
                print("Warning: Could not set Japanese font. Japanese text may not display correctly.")
    
    # マイナス記号の文字化け対策
    plt.rcParams['axes.unicode_minus'] = False
    
    print(f"Font set to: {plt.rcParams['font.family']}")


def get_available_fonts():
    """
    利用可能なフォントのリストを取得
    
    Returns
    -------
    list
        利用可能なフォント名のリスト
    """
    import matplotlib.font_manager as fm
    
    fonts = [f.name for f in fm.fontManager.ttflist]
    japanese_fonts = [f for f in fonts if any(
        keyword in f for keyword in ['Gothic', 'Mincho', 'Meiryo', 'Yu', 'MS', 'Hiragino', 'Noto', 'IPA']
    )]
    
    return sorted(set(japanese_fonts))


if __name__ == "__main__":
    print("Available Japanese fonts:")
    for font in get_available_fonts():
        print(f"  - {font}")
    
    print("\nSetting up Japanese font...")
    setup_japanese_font()
    
    # テスト
    plt.figure(figsize=(8, 6))
    plt.plot([1, 2, 3], [1, 4, 9])
    plt.title('日本語テスト - Japanese Test')
    plt.xlabel('横軸 (X-axis)')
    plt.ylabel('縦軸 (Y-axis)')
    plt.savefig('font_test.png', dpi=150, bbox_inches='tight')
    print("\nTest image saved as 'font_test.png'")
    plt.close()
