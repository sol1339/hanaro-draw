import tempfile
import unittest
from pathlib import Path
from collections import Counter
from draw_store import DrawStore
from unittest.mock import Mock

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.path=Path(self.temp.name)/'test.db'; self.s=DrawStore(self.path)
    def tearDown(self):
        self.s.db.close(); self.temp.cleanup()
    def test_full_pool(self):
        self.s.configure(20,[(f'상품{i}',q) for i,q in enumerate([1,2,4]+[0]*7)])
        counts=Counter(self.s.draw()[1] for _ in range(20))
        self.assertEqual(counts, {0:13,1:1,2:2,3:4})
        with self.assertRaises(ValueError): self.s.draw()
        self.assertEqual(len(self.s.history()),20)
    def test_invalid_rollback(self):
        before=self.s.rows()
        with self.assertRaises(ValueError): self.s.configure(1,[('상품',2)]*10)
        self.assertEqual(before,self.s.rows())
        self.s.draw(lambda n: 0)
        with self.assertRaises(ValueError): self.s.configure(7,[('상품',q) for q in [1,2,4]+[0]*7])
        self.assertEqual(self.s.rows()[0][3],1)
    def test_persistence_and_boundaries(self):
        result=self.s.draw(lambda n:n-1)
        self.assertEqual(result[1],3)
        self.s.db.close(); self.s=DrawStore(self.path)
        self.assertEqual(self.s.history()[0][0],result[0])
        self.assertEqual(sum(q-u for _,_,q,u in self.s.rows()),19999)
    def test_reset_preserves_configuration(self):
        self.s.configure(12, [('선물', 1)] * 10)
        before = [(r,n,q) for r,n,q,u in self.s.rows()]
        for _ in range(12): self.s.draw()
        self.s.reset()
        self.assertEqual(self.s.history(), [])
        self.assertEqual([(r,n,q) for r,n,q,u in self.s.rows()], before)
        self.assertTrue(all(u == 0 for r,n,q,u in self.s.rows()))
        self.assertEqual(self.s.draw()[0], 1)
        self.s.db.close(); self.s = DrawStore(self.path)
        self.assertEqual(sum(q-u for r,n,q,u in self.s.rows()), 11)

    def test_two_connections(self):
        other=DrawStore(self.path)
        self.s.configure(1,[('상품',1)]+[('상품',0)]*9)
        self.assertEqual(other.draw()[1],1)
        with self.assertRaises(ValueError): self.s.draw()
        other.db.close()

if __name__=='__main__': unittest.main()
