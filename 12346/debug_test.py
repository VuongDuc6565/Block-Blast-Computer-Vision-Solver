"""Debug script to test calculatePositions.calculate()"""
import traceback

try:
    import calculatePositions
    print("1. Module imported successfully")
    
    print("2. Testing calculate function...")
    output, blocks, coordsUsed, board = calculatePositions.calculate(0)
    print(f"3. Success! Board shape: {board.shape}")
    print(f"   Blocks found: {len(blocks)}")
    print(f"   Output solutions: {len(output)}")
except Exception as e:
    print(f"\nERROR: {type(e).__name__}: {e}")
    traceback.print_exc()
