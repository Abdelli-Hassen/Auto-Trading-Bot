# Trading Bot Batch Files

Quick-start scripts for running the Autonomous Trading System on Windows.

## Files Overview

### 1. **start.bat** - Main Application
Starts the trading bot in normal mode.

```bash
start.bat
```

**Features:**
- ✅ Verifies Python installation
- ✅ Checks project structure
- ✅ Loads design system automatically
- ✅ Shows startup information
- ✅ Reports exit status

**Use when:** You want to run the trading bot normally

---

### 2. **debug.bat** - Development Mode
Starts the bot with extra debugging information and keeps the console open.

```bash
debug.bat
```

**Features:**
- ✅ Verbose output
- ✅ Shows system information
- ✅ Displays Python version
- ✅ Console stays open for inspection
- ✅ Better error visibility

**Use when:** You want to debug or watch the application run

---

### 3. **backtest.bat** - Backtesting
Runs historical backtests of the trading strategy.

```bash
backtest.bat
```

**Features:**
- ✅ Executes `run_backtest.py`
- ✅ Generates equity curves
- ✅ Saves trade logs
- ✅ Reports output file locations

**Output files:**
- `backtest_equity.csv` - Equity curve over time
- `backtest_trades.csv` - Individual trade records

**Use when:** You want to test the strategy on historical data

---

### 4. **test.bat** - Test Suite
Runs all system and design system tests.

```bash
test.bat
```

**Features:**
- ✅ Runs design system tests
- ✅ Runs system tests
- ✅ Shows test summary
- ✅ Reports pass/fail status

**Output:**
- Design System Tests: Validates design file structure
- System Tests: Validates trading system components

**Use when:** You want to verify everything is working correctly

---

## Quick Start

### First Time Setup

1. **Install Python** (if not already installed)
   - Download from https://www.python.org/
   - During installation, check "Add Python to PATH"

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Tests** (optional but recommended)
   ```bash
   test.bat
   ```

### Start Trading Bot

**Normal Mode:**
```bash
start.bat
```

**Debug Mode** (see detailed output):
```bash
debug.bat
```

### Run Backtest

```bash
backtest.bat
```

### Run Tests

```bash
test.bat
```

---

## Understanding Output

### Startup Information
```
============================================================
          AUTONOMOUS TRADING SYSTEM - STARTUP
============================================================

Script Location: D:\Projects\Trading\trading_bot
Timestamp: 04/28/2026 14:32:01
```

### Status Checks
```
Checking Python installation...
Python 3.11.0

Checking project files...
✓ main.py found
✓ config.py found
✓ Design system replica found
```

### Project Structure Verification
```
Project Structure:
  ✓ data/
  ✓ strategies/
  ✓ execution/
  ✓ risk/
  ✓ backtest/
  ✓ monitoring/
  ✓ utils/
```

### Exit Status
```
============================================================
Application exited successfully
============================================================
```

---

## Troubleshooting

### "Python is not installed or not in PATH"
**Solution:**
1. Install Python from https://www.python.org/
2. During installation, check "Add Python to PATH"
3. Restart your computer or restart the command prompt

### "main.py not found"
**Solution:**
1. Make sure you're running the .bat file from the trading_bot directory
2. Verify that main.py exists in the same folder as the .bat file

### Application crashes
**Solution:**
1. Run `debug.bat` to see detailed error messages
2. Check that all dependencies are installed: `pip install -r requirements.txt`
3. Review the log file: `logs/main.log`

### "ERROR: config.py not found"
**Note:** This is just a warning. The system will use default configuration.
**To fix:** Create a config.py file or copy from example_usage.py

---

## Advanced Usage

### Keep Console Open After Exit
Edit any .bat file and uncomment the last `pause` command:

```batch
REM Uncomment to keep window open
pause

endlocal
exit /b %EXIT_CODE%
```

### Pass Custom Arguments
Create a custom batch file or modify start.bat to pass arguments:

```batch
python main.py --testnet --config custom_config.py
```

### Scheduled Execution
Use Windows Task Scheduler to run the bot automatically:

1. Open Task Scheduler (Windows key + R, type "taskschd.msc")
2. Create new task
3. Set trigger (daily, hourly, etc.)
4. Set action to run: `D:\Projects\Trading\trading_bot\start.bat`

---

## File Details

| File | Size | Purpose | Run Time |
|------|------|---------|----------|
| start.bat | ~2 KB | Normal execution | Depends on bot |
| debug.bat | ~2 KB | Development mode | Depends on bot |
| backtest.bat | ~1 KB | Historical testing | 1-10 minutes |
| test.bat | ~2 KB | System validation | 1-2 minutes |

---

## Environment Variables

These batch files use standard Windows environment variables:

- `%~dp0` - Directory of the batch file
- `%errorlevel%` - Exit code from last command
- `%date%` - Current date
- `%time%` - Current time
- `%OS%` - Operating system name

---

## Logging

All output is printed to console and also saved to log files:

- **Main application:** `logs/main.log`
- **Backtest results:** `backtest_equity.csv`, `backtest_trades.csv`
- **Test results:** Shown in console

---

## Integration with IDEs

You can also run these directly from your IDE:

**Visual Studio Code:**
1. Open terminal (Ctrl + `)
2. Type: `.\start.bat`

**PyCharm:**
1. Tools → Create Command-line Launcher
2. Right-click on any .bat file → Run

---

## Exit Codes

- `0` - Success
- `1` - Error (Python not found, file missing, etc.)
- Other codes - See error message in console

---

## Security Note

These batch files:
- ✅ Do not modify system files
- ✅ Do not modify registry
- ✅ Do not require administrator privileges
- ✅ Only run Python code from this project
- ✅ Are safe to run on any Windows computer

---

## Getting Help

1. **Check Status:** Run `test.bat`
2. **Debug:** Run `debug.bat` and watch for errors
3. **Review Logs:** Check `logs/main.log`
4. **Read Documentation:** See README.md and other .md files

---

## Summary

| Task | Command |
|------|---------|
| Start bot | `start.bat` |
| Debug bot | `debug.bat` |
| Run backtest | `backtest.bat` |
| Run tests | `test.bat` |
| Check Python | `python --version` |
| Install deps | `pip install -r requirements.txt` |

That's all! The .bat files handle the rest.
