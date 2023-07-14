import tiktoken
import inspect
classes = inspect.getmembers(tiktoken, inspect.isclass)
for name, obj in classes:
    print(name)
try:
    from tiktoken import Token
    print("Token class exists")
except ImportError:
    print("Token class does not exist")

try:
    from tiktoken import TokenList
    print("TokenList class exists")
except ImportError:
    print("TokenList class does not exist")
