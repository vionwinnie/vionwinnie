# Source : https://stackoverflow.com/questions/19924104/python-multiprocessing-handling-child-errors-in-parent

import multiprocessing
import traceback

from time import sleep


class Process(multiprocessing.Process):
    """
    Class which returns child Exceptions to Parent.
    https://stackoverflow.com/a/33599967/4992248
    """

    def __init__(self, *args, **kwargs):
        multiprocessing.Process.__init__(self, *args, **kwargs)
        self._parent_conn, self._child_conn = multiprocessing.Pipe()
        self._exception = None

    def run(self):
        try:
            multiprocessing.Process.run(self)
            self._child_conn.send(None)
        except Exception as e:
            tb = traceback.format_exc()
            self._child_conn.send((e, tb))
            # raise e  # You can still rise this exception if you need to

    @property
    def exception(self):
        if self._parent_conn.poll():
            self._exception = self._parent_conn.recv()
        return self._exception


class Task_1:
    def do_something(self, queue):
        queue.put(dict(users=2))


class Task_2:
    def do_something(self, queue):
        queue.put(dict(users=5))


def main():
    try:
        task_1 = Task_1()
        task_2 = Task_2()

        # Example of multiprocessing which is used:
        # https://eli.thegreenplace.net/2012/01/16/python-parallelizing-cpu-bound-tasks-with-multiprocessing/
        task_1_queue = multiprocessing.Queue()
        task_2_queue = multiprocessing.Queue()

        task_1_process = Process(
            target=task_1.do_something,
            kwargs=dict(queue=task_1_queue))

        task_2_process = Process(
            target=task_2.do_something,
            kwargs=dict(queue=task_2_queue))

        task_1_process.start()
        task_2_process.start()

        while task_1_process.is_alive() or task_2_process.is_alive():
            sleep(10)

            if task_1_process.exception:
                error, task_1_traceback = task_1_process.exception

                # Do not wait until task_2 is finished
                task_2_process.terminate()

                raise ChildProcessError(task_1_traceback)

            if task_2_process.exception:
                error, task_2_traceback = task_2_process.exception

                # Do not wait until task_1 is finished
                task_1_process.terminate()

                raise ChildProcessError(task_2_traceback)

        task_1_process.join()
        task_2_process.join()

        task_1_results = task_1_queue.get()
        task_2_results = task_2_queue.get()

        task_1_users = task_1_results['users']
        task_2_users = task_2_results['users']

    except Exception:
        # Here usually I send email notification with error.
        print('traceback:', traceback.format_exc())


if __name__ == "__main__":
    main()
