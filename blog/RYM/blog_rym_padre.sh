#! /usr/bin/env bash

# Telegram Bot Configuration
source /home/pi/hugo/hugo_scripts/blog/RYM/.env

TELEGRAM_BOT_TOKEN="$1"
TELEGRAM_CHAT_ID="$2"

# Function to send Telegram message
send_telegram_message() {
    local message="$1"
    local parse_mode="${2:-}"
    
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
         -d "chat_id=$TELEGRAM_CHAT_ID" \
         -d "text=$message" \
         ${parse_mode:+-d "parse_mode=$parse_mode"}
}


# Capture script output
exec > >(tee -a /tmp/rym_script_log.txt) 2>&1

blog_dir="$HOME/hugo/web/rym"
fecha="$(date +%d-%m-%ys)"

# Initialize script run flags
monthly_script_ran=false
yearly_script_ran=false
weekly_script_ran=false

cd "$blog_dir" || {
    send_telegram_message "❌ Failed to change directory to $blog_dir"
    exit 1
}

# Weekly script execution
weekly_script() {
    hugo new --kind posts posts/$fecha.md
    semanal="/home/pi/hugo/web/rym/content/semanal/$fecha.md"
    source "$HOME/scripts/python_venv/bin/activate"

    python3 "$HOME/hugo/hugo_scripts/blog/RYM/blog_rym.py" || {
        send_telegram_message "❌ Error in blog_rym.py. Check log at /tmp/rym_script_log.txt" "Markdown"
        return 1
    }

    echo '<!--more-->' >> "$semanal"
    sed "s/title/title \= $fecha/" 
    #sed 's/tipo/semanal: true/' "/home/pi/hugo/web/rym/content/posts/$fecha.md"
    cat "/home/pi/hugo/web/rym/lastfm_weekly_stats.md" >> "$semanal"

    #send_telegram_message "✅ Weekly RYM script completed successfully for $fecha" "Markdown"
    weekly_script_ran=true
}


# Monthly script execution
monthly_script() {
    hoy=$(date +%d)
    dia_semana="$(date +%A)"
    mes="$(date +%B-%y)"
    
    # Existing monthly script logic
    # Obtain last Sunday of the month logic here...
    if ["$hoy" > "24"} && [ "$dia_semana" == "domingo" ]; then
        cd "$blog_dir" || exit 0
        hugo new --kind posts mensual/$mes.md
        python3 "$HOME/hugo/hugo_scripts/blog/RYM/blog_rym_mensual.py"
        #sed 's/tipo/mensual: true/' "/home/pi/hugo/web/rym/content/mensual/$mes.md"
        cat "/home/pi/hugo/web/rym/lastfm_monthly_stats.md" >> "/home/pi/hugo/web/rym/content/mensual/$mes.md"
        monthly_script_ran=true
    fi
}

# Yearly script execution
yearly_script() {
    hoy="$(date +%m-%d)"
    anio="$(date +%Y)"

    if [ "$hoy" == "01-01" ]; then
        cd "$blog_dir" || exit 0
        hugo new --kind posts anual/$anio.md
        #sed 's/tipo/anual: true/' "/home/pi/hugo/web/rym/content/anual/$anio.md"
        python3 "$HOME/hugo/hugo_scripts/blog/RYM/blog_rym_anual.py"
        cat "/home/pi/hugo/web/rym/lastfm_yearly_stats.md" >> "/home/pi/hugo/web/rym/content/anual/$anio.md"
        yearly_script_ran=true
    fi
}

# Main execution block
if weekly_script; then
    monthly_script
    yearly_script

    # Send notifications for monthly and yearly scripts
    if $weekly_script_ran; then
        send_telegram_message "✅ Weekly script executed successfully" "Markdown"
    else
        send_telegram_message "❌ Weekly script error" "Markdown"
    fi

    if $monthly_script_ran; then
        send_telegram_message "✅ Monthly script executed successfully" "Markdown"
    fi

    if $yearly_script_ran; then
        send_telegram_message "✅ Yearly script executed successfully" "Markdown"
    fi
else
    send_telegram_message "❌ Weekly script failed. Stopping execution." "Markdown"
fi

cd "$blog_dir" || exit 0 ; git add . ; git commit -m "" ; git push