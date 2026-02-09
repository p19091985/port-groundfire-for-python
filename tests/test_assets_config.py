
import unittest
import os
import sys
import glob
import pygame

# Ensure src is in path
sys.path.append(os.getcwd())
from src.inifile import ReadIniFile

class TestAssetsConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Prevent pygame from opening a window
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        # Initialize mixer for WAV testing (frequency, size, channels, buffer)
        # Standard Groundfire init: 22050Hz, 16bit, stereo
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
        except Exception:
            pass # CI environments might fail audio init even with dummy driver

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_tga_assets_validity(self):
        """Verify all TGA files in data/ can be loaded and have valid headers."""
        data_dir = os.path.join(os.getcwd(), 'data')
        tga_files = glob.glob(os.path.join(data_dir, '*.tga'))
        
        self.assertTrue(len(tga_files) > 0, "No TGA files found in data/ directory")

        for tga_path in tga_files:
            with self.subTest(file=os.path.basename(tga_path)):
                try:
                    # Attempt to load with pygame
                    surf = pygame.image.load(tga_path)
                    
                    # Verify dimensions are non-zero
                    width, height = surf.get_size()
                    self.assertGreater(width, 0, f"Width is 0 for {tga_path}")
                    self.assertGreater(height, 0, f"Height is 0 for {tga_path}")
                    
                    # Optional: Verify power of 2 dimensions if OpenGL requires it (C++ usually did)
                    # Groundfire C++ used OpenGL 1.1 textures which often required POT.
                    # But for now, valid loading is the benchmark.
                except pygame.error as e:
                    self.fail(f"Failed to load TGA {tga_path}: {e}")

    def test_wav_assets_validity(self):
        """Verify all WAV files in data/ can be loaded by mixer."""
        data_dir = os.path.join(os.getcwd(), 'data')
        wav_files = glob.glob(os.path.join(data_dir, '*.wav'))
        
        self.assertTrue(len(wav_files) > 0, "No WAV files found in data/ directory")

        for wav_path in wav_files:
            with self.subTest(file=os.path.basename(wav_path)):
                try:
                    # Attempt to load sound
                    sound = pygame.mixer.Sound(wav_path)
                    self.assertIsNotNone(sound)
                    # Just getting length is enough to prove decoded
                    length = sound.get_length()
                    self.assertGreater(length, 0.0, f"Sound length is 0 for {wav_path}")
                except Exception as e:
                    # Some CI might not have audio device, but pygame dummy driver usually allows loading.
                    # If mixer init failed, skip
                    if not pygame.mixer.get_init():
                        self.skipTest("Pygame Mixer not initialized")
                    self.fail(f"Failed to load WAV {wav_path}: {e}")

    def test_ini_parsing_options(self):
        """Verify reading of conf/options.ini matches expectation."""
        ini_path = os.path.join(os.getcwd(), 'conf', 'options.ini')
        self.assertTrue(os.path.exists(ini_path), "conf/options.ini missing")

        ini = ReadIniFile(ini_path)

        # Check [Screen] section, vital for startup
        # C++ defaults: Width=800, Height=600, Fullscreen=0
        width = ini.get_int("Screen", "Width", 640)
        height = ini.get_int("Screen", "Height", 480)
        fullscreen = ini.get_int("Screen", "Fullscreen", 1)

        # We expect sane values, not just defaults (unless config IS default)
        self.assertIsInstance(width, int)
        self.assertIsInstance(height, int)
        
        # Check a string value
        # [Missile] Fuel=3.0 (Float usually but read as string to test string getter)
        missile_fuel = ini.get_string("Missile", "Fuel", "Default")
        self.assertNotEqual(missile_fuel, "Default", "Failed to read Missile Fuel string")

    def test_ini_parsing_strict_types(self):
        """Verify strict typing (int vs float behavior) in ReadIniFile."""
        # Create a temp ini file for strict testing (Mocking file system or just creating temp file)
        import tempfile
        
        content = """[Test]
IntVal=42
FloatVal=3.14159
StringVal=Hello World
BadInt=NotAnInt
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            ini = ReadIniFile(tmp_path)
            
            # 1. Valid Int
            val = ini.get_int("Test", "IntVal", -1)
            self.assertEqual(val, 42)
            
            # 2. Valid Float
            fval = ini.get_float("Test", "FloatVal", -1.0)
            self.assertAlmostEqual(fval, 3.14159, places=5)
            
            # 3. String
            sval = ini.get_string("Test", "StringVal", "Fail")
            self.assertEqual(sval, "Hello World")
            
            # 4. Bad Int (Should verify error handling/default value logic matches C++)
            # C++ uses atoi/atof. atoi("NotAnInt") usually returns 0. 
            # Python int("NotAnInt") raises ValueError.
            # Our python implementation catches ValueError and returns default.
            bad_val = ini.get_int("Test", "BadInt", 999)
            self.assertEqual(bad_val, 999, "Should return default on parsing failure")
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == '__main__':
    unittest.main()
