#!/usr/bin/env bash
set -euo pipefail

mode=${1:-output}
picture_dir=$(xdg-user-dir PICTURES)
if [[ -z $picture_dir ]]; then
    picture_dir=$HOME/Pictures
fi
save_dir=${picture_dir%/}/Screenshots
mkdir -p -- "$save_dir"
file=$save_dir/$(date +'%Y-%m-%d_%H-%M-%S_%N').png

case $mode in
    region)
        # An Escape in slurp cancels the screenshot quietly.
        if ! geometry=$(slurp); then
            exit 0
        fi
        [[ -n $geometry ]] || exit 0
        # Let Sway render a frame after slurp removes its selection overlay.
        sleep 0.25
        grim -g "$geometry" "$file"
        ;;
    window)
        geometry=$(swaymsg -t get_tree -r | jq -er '
            .. | objects | select(.focused? == true and .rect? != null)
            | .rect | "\(.x),\(.y) \(.width)x\(.height)"
        ')
        grim -g "$geometry" "$file"
        ;;
    output)
        output=$(swaymsg -t get_outputs -r | jq -er '.[] | select(.focused == true) | .name')
        grim -o "$output" "$file"
        ;;
    *)
        printf 'Usage: %s {region|window|output}\n' "$0" >&2
        exit 2
        ;;
esac

wl-copy --type image/png < "$file"
notify-send -a Screenshot -i camera-photo 'Снимок сохранён' "$file"
