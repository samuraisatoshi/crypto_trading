#!/bin/bash

# Function to show usage
show_usage() {
    echo "Usage: ./view_logs.sh [option]"
    echo "Options:"
    echo "  -f, --follow    Monitor logs in real-time (like tail -f)"
    echo "  -l, --last      Show last 50 lines of logs"
    echo "  -e, --errors    Show only ERROR level logs"
    echo "  -w, --warnings  Show WARNING and ERROR level logs"
    echo "  -d, --data      Show data processing logs (enrichment, download, etc.)"
    echo "  -b, --backtest  Show backtest logs"
    echo "  -s, --storage   Show storage operation logs"
    echo "  -h, --help      Show this help message"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Default log file
LOG_FILE="$SCRIPT_DIR/logs/ml_trade.log"

# Function to show data processing logs
show_data_logs() {
    echo "=== Data Processing Summary ==="
    echo
    echo "Enrichment Process:"
    echo "------------------"
    grep "Starting data enrichment process\|Initial rows\|Final rows\|Added columns" "$LOG_FILE" | awk '
    BEGIN {
        printf "%-25s %-15s %-15s %-15s\n", "TIMESTAMP", "INITIAL", "FINAL", "ADDED COLS"
        printf "%-25s %-15s %-15s %-15s\n", "---------", "-------", "-----", "----------"
    }
    {
        timestamp=$1" "$2
        if ($0 ~ /Initial rows/) initial=$NF
        else if ($0 ~ /Final rows/) final=$NF
        else if ($0 ~ /Added columns/) {
            cols=$NF
            printf "%-25s %-15s %-15s %-15s\n", timestamp, initial, final, cols
        }
    }'
    
    echo
    echo "Added Features:"
    echo "--------------"
    grep "Added" "$LOG_FILE" | grep -v "columns\|rows" | awk '{
        if ($1 == "-") {
            feature=substr($0, 3)
            printf "  %s\n", feature
        }
    }'
}

# Function to show backtest logs
show_backtest_logs() {
    echo "=== Backtest Summary ==="
    echo
    echo "Strategy Performance:"
    echo "--------------------"
    grep "Strategy\|Trade\|PnL" "$LOG_FILE" | awk '
    BEGIN {
        trades=0
        wins=0
        total_pnl=0
    }
    {
        if ($0 ~ /Trade executed/) {
            trades++
            if ($0 ~ /profit/) wins++
            split($0, arr, "PnL: ")
            if (length(arr) > 1) {
                pnl=arr[2]+0
                total_pnl+=pnl
            }
        }
    }
    END {
        if (trades > 0) {
            printf "Total Trades : %d\n", trades
            printf "Win Rate     : %.1f%%\n", (wins/trades)*100
            printf "Total PnL    : %.2f\n", total_pnl
            printf "Avg PnL/Trade: %.2f\n", total_pnl/trades
        } else {
            print "No trades found"
        }
    }'
}

# Function to show storage logs
show_storage_logs() {
    echo "=== Storage Operations Summary ==="
    echo
    echo "File Operations:"
    echo "----------------"
    grep "Saving\|Loading\|Downloading\|Uploading" "$LOG_FILE" | awk '
    BEGIN {
        printf "%-25s %-12s %-40s\n", "TIMESTAMP", "OPERATION", "FILE"
        printf "%-25s %-12s %-40s\n", "---------", "---------", "----"
    }
    {
        timestamp=$1" "$2
        operation=$3
        file=substr($0, index($0,$4))
        printf "%-25s %-12s %-40s\n", timestamp, operation, file
    }'
    
    echo
    echo "Storage Statistics:"
    echo "------------------"
    grep "bytes\|files" "$LOG_FILE" | awk '
    BEGIN {
        total_bytes=0
        total_files=0
    }
    {
        if ($0 ~ /bytes/) {
            bytes=$1
            total_bytes+=bytes
        }
        if ($0 ~ /files processed/) {
            files=$1
            total_files+=files
        }
    }
    END {
        if (total_bytes > 0 || total_files > 0) {
            printf "Total Data Processed: %.2f MB\n", total_bytes/1024/1024
            printf "Total Files Handled : %d\n", total_files
        } else {
            print "No storage statistics found"
        }
    }'
}

case "$1" in
    -f|--follow)
        echo "Monitoring logs in real-time (Ctrl+C to exit)..."
        tail -f "$LOG_FILE"
        ;;
    -l|--last)
        echo "Last 50 log entries:"
        tail -n 50 "$LOG_FILE"
        ;;
    -e|--errors)
        echo "ERROR level logs:"
        grep "ERROR" "$LOG_FILE"
        ;;
    -w|--warnings)
        echo "WARNING and ERROR level logs:"
        grep -E "WARNING|ERROR" "$LOG_FILE"
        ;;
    -d|--data)
        show_data_logs
        ;;
    -b|--backtest)
        show_backtest_logs
        ;;
    -s|--storage)
        show_storage_logs
        ;;
    -h|--help)
        show_usage
        ;;
    *)
        show_usage
        ;;
esac
