[[ $- != *i* ]] && return

export PATH="$HOME/.local/bin:$HOME/.tayowrld-bin:$PATH:$HOME/.cargo/bin:$HOME/.npm/bin"

# Searchable history, shared across open terminals.
HISTSIZE=20000
HISTFILESIZE=50000
HISTCONTROL=ignoreboth:erasedups
HISTTIMEFORMAT='%F %T  '
shopt -s histappend checkwinsize cdspell

# Tab completion and prefix-aware Up/Down history search.
bind 'set completion-ignore-case on'
bind 'set show-all-if-ambiguous on'
bind 'set colored-stats on'
bind 'set mark-symlinked-directories on'
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'
bind '"\e[1;5C": forward-word'
bind '"\e[1;5D": backward-word'

alias ls='eza --tree --level=1 --hyperlink -@ -l --time-style relative --no-permissions'
alias ll='eza --tree --level=1 --hyperlink -@ -lhA --time-style relative'
alias la='eza --tree --level=1 --hyperlink -@ -lA --time-style relative --no-permissions'
alias grep='grep --color=auto'
alias ..='cd ..'
alias ...='cd ../..'
alias g='git'
alias gs='git status -sb'
alias gd='git diff'
alias gds='git diff --staged'
alias gl='git log --oneline --decorate -12'

compress-web() {
	ffmpeg -i "$1" \
		-vf "scale=1920:1080:flags=lanczos,unsharp=5:5:0.4:5:5:0" \
		-c:v libx264 \
		-preset veryfast \
		-crf 24 \
		-pix_fmt yuv420p \
		-c:a aac -b:a 96k \
		-movflags +faststart \
		"$1.mp4"
}

cd(){
	builtin cd "$@" || return
	if command -v here >/dev/null; then here .; fi
}

mkcd() { mkdir -p -- "$1" && cd -- "$1"; }
croot() {
  local root
  root=$(git rev-parse --show-toplevel 2>/dev/null) || return 1
  cd -- "$root"
}

# Git's installed prompt helper handles branches, detached HEAD and worktrees.
if [[ -r /usr/share/git/completion/git-prompt.sh || -r /usr/share/git-core/contrib/completion/git-prompt.sh ]]; then
  if [[ -r /usr/share/git/completion/git-prompt.sh ]]; then
    . /usr/share/git/completion/git-prompt.sh
  else
    . /usr/share/git-core/contrib/completion/git-prompt.sh
  fi
  GIT_PS1_SHOWDIRTYSTATE=1
  GIT_PS1_SHOWUNTRACKEDFILES=1
fi

# Branch names and paths can contain shell metacharacters; keep prompt text literal.
shopt -u promptvars

__pretty_prompt() {
  local last_status=$? git_info='' reset lilac pink blue green red
  history -a
  history -n

  if [[ ${TERM:-dumb} == dumb ]]; then
    PS1='[\u@\h \w]\$ '
    return
  fi

  reset='\[\e[0m\]'
  lilac='\[\e[38;2;149;119;161m\]'
  pink='\[\e[38;2;173;105;120m\]'
  blue='\[\e[38;2;106;131;164m\]'
  green='\[\e[38;2;102;139;125m\]'
  red='\[\e[38;2;189;125;137m\]'

  if declare -F __git_ps1 >/dev/null; then
    git_info=$(__git_ps1 ' %s')
  fi

  PS1="${lilac}${reset} ${pink}\\u@\\h${reset} ${lilac}in${reset} ${blue}\\w${reset}"
  [[ -n $git_info ]] && PS1+=" ${green}${git_info}${reset}"
  (( last_status != 0 )) && PS1+=" ${red}✗ ${last_status}${reset}"
  PS1+="\n${lilac}${reset} ${pink}>${reset} "
}

# Keep the system's terminal-title hook and run our hook first to see exit status.
_pretty_hook_found=0
for _pretty_hook in "${PROMPT_COMMAND[@]}"; do
  [[ $_pretty_hook == __pretty_prompt ]] && _pretty_hook_found=1
done
if (( ! _pretty_hook_found )); then
  PROMPT_COMMAND=(__pretty_prompt "${PROMPT_COMMAND[@]}")
fi
unset _pretty_hook _pretty_hook_found
