

class SingletonVerifierMeta(type):
    def __init__(cls, clsname, bases, clsdict):
        # for key, value in clsdict.items():
        #     print(key, value)
        #     if key == '__init__':
        #         print(dis.dis(value))
        cls._instance = None
        type.__init__(cls, clsname, bases, clsdict)

    def __call__(cls, *args, **kwargs):
        if cls._instance ==None:
            # print("first instance")
            cls._instance = super().__call__(*args, **kwargs)
            return cls._instance
        else:
            # print("second instance")
            return cls._instance



class SingletonVerifier(metaclass=SingletonVerifierMeta):
    pass
