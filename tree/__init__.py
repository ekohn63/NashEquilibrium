if __name__ == "__main__" and __package__ == None: 
    from sys import path
    import os.path
    path.append(os.path.dirname(path[0]))
    print(os.path.dirname(path[0]))
    print(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    __package__ = "examples"