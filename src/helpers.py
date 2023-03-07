
import unicodedata

escape_str = ['.', '!', '<', '>', '_', '*', '[', ']', '(', ')', '~', '`', '#', '+', '-', '=', '|', '{', '}']


def to_half_width(text: str) -> str:
    text = text.replace('\u3000', ' ')
    return unicodedata.normalize('NFKC', text)


def escape(string: str) -> str:
    # string = to_half_width(string)

    return  ''.join(map(lambda char: string.replace(char, f'\\{char}'), escape_str))


if __name__ == '__main__':
  string = '\n\n这是正确的shell判断方法。如果当前操作系统架构是x86_64，并且yasm命令不可用，则会安装yasm。 \n\n解释一下代码：\n\n- $(arch)：获取当前操作系统架构。\n- "x86_64"：期望的操作系统架构。\n- ! command -v yasm &> /dev/null：通过检查yasm命令是否可用来判断yasm是否已安装。如果yasm已安装，则此条件为假，否则为真。\n- brew install yasm &> /dev/null：如果yasm未安装，则安装yasm。 &> /dev/null 用于将所有输出重定向到/dev/null，以防止生成任何输出。\n\n因此，此代码可确保在需要时安装yasm。'
  print(escape(string))
