from chain.validators import Validators

class Permissions():

    def set_dag(self, dag):
        self.dag = dag

    def get_pemission(self, i):
        if not hasattr(self, 'validators'):
            self.validators = Validators()
        item = i % self.validators.get_size()
        return self.validators.get_by_i(item)
