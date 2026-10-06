# bash completion for identicon

_identicon()
{
	local cur prev words cword
	_init_completion || return

	case $prev in
	-s | --salt | -S | --size | -b | --backcolor)
		return
		;;
	-o | --out)
		_filedir
		return
		;;
	-t | --type)
		COMPREPLY=($(compgen -W 'identicon wavatar monsterid retro robo' -- "$cur"))
		return
		;;
	-F | --format)
		COMPREPLY=($(compgen -W 'png jpg jpeg gif bmp webp tiff ico' -- "$cur"))
		return
		;;
	esac

	if [[ $cur == -* ]]; then
		COMPREPLY=($(compgen -W '-s --salt -o --out -t --type -F --format -S --size -b --backcolor -f --force -v --verbose -q --quiet -h --help --version' -- "$cur"))
		return
	fi
}

complete -F _identicon identicon
