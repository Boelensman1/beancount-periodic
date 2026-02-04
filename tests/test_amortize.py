import datetime
import unittest

from beancount.core.compare import compare_entries
from beancount.core.data import Transaction
from beancount.loader import load_string

import tests.util


def tx_normal(date: datetime.date, narration: str) -> Transaction:
    return tests.util.make_transaction(
        date=date,
        payee='Landlord',
        narration=narration,
        account_from='Liabilities:CreditCard:0001',
        account_to='Equity:Amortization:Home:Rent',
        amount='12000',
    )


def tx_amortized(date: datetime.date, narration: str) -> Transaction:
    return tests.util.make_transaction(
        date=date,
        payee='Landlord',
        narration=narration,
        account_from='Equity:Amortization:Home:Rent',
        account_to='Expenses:Home:Rent',
        amount='1000',
    )


def tx_prepaid(date: datetime.date, narration: str) -> Transaction:
    return tests.util.make_transaction(
        date=date,
        payee='Insurance Co',
        narration=narration,
        account_from='Liabilities:CreditCard:0001',
        account_to='Assets:Prepaid:Insurance',
        amount='1200',
    )


def tx_amortized_prepaid(date: datetime.date, narration: str) -> Transaction:
    return tests.util.make_transaction(
        date=date,
        payee='Insurance Co',
        narration=narration,
        account_from='Assets:Prepaid:Insurance',
        account_to='Expenses:Insurance',
        amount='100',
    )


class AmortizeTest(unittest.TestCase):
    def test_simple(self):
        journal_str = """
plugin "beancount_periodic.amortize"
1900-01-01 open Liabilities:CreditCard:0001 USD
1900-01-01 open Expenses:Home:Rent USD
1900-01-01 open Equity:Amortization:Home:Rent USD
2022-03-31 * "Landlord" "2022-04 Rent"
  Liabilities:CreditCard:0001    -12000 USD
  Expenses:Home:Rent
    amortize: "1 Year @2022-04-01 /Monthly"
"""
        entries, errors, options_map = load_string(journal_str)
        self.assertEqual(len(errors), 0)

        expected_entries = [
            tx_normal(datetime.date(2022, 3, 31), '2022-04 Rent'),
            tx_amortized(datetime.date(2022, 4, 1), '2022-04 Rent Amortized(1/12)'),
            tx_amortized(datetime.date(2022, 5, 1), '2022-04 Rent Amortized(2/12)'),
            tx_amortized(datetime.date(2022, 6, 1), '2022-04 Rent Amortized(3/12)'),
            tx_amortized(datetime.date(2022, 7, 1), '2022-04 Rent Amortized(4/12)'),
            tx_amortized(datetime.date(2022, 8, 1), '2022-04 Rent Amortized(5/12)'),
            tx_amortized(datetime.date(2022, 9, 1), '2022-04 Rent Amortized(6/12)'),
            tx_amortized(datetime.date(2022, 10, 1), '2022-04 Rent Amortized(7/12)'),
            tx_amortized(datetime.date(2022, 11, 1), '2022-04 Rent Amortized(8/12)'),
            tx_amortized(datetime.date(2022, 12, 1), '2022-04 Rent Amortized(9/12)'),
            tx_amortized(datetime.date(2023, 1, 1), '2022-04 Rent Amortized(10/12)'),
            tx_amortized(datetime.date(2023, 2, 1), '2022-04 Rent Amortized(11/12)'),
            tx_amortized(datetime.date(2023, 3, 1), '2022-04 Rent Amortized(12/12)'),
        ]

        same, missing1, missing2 = compare_entries(list(tests.util.get_transactions_cleaned(entries)), expected_entries)
        self.assertTrue(same)

    def test_generate_until_01(self):
        journal_str = """
plugin "beancount_periodic.amortize" "{'generate_until':'2022-10-01'}"
1900-01-01 open Liabilities:CreditCard:0001 USD
1900-01-01 open Expenses:Home:Rent USD
1900-01-01 open Equity:Amortization:Home:Rent USD
2022-03-31 * "Landlord" "2022-04 Rent"
  Liabilities:CreditCard:0001    -12000 USD
  Expenses:Home:Rent
    amortize: "1 Year @2022-04-01 /Monthly"
        """
        entries, errors, options_map = load_string(journal_str)
        self.assertEqual(len(errors), 0)

        expected_entries = [
            tx_normal(datetime.date(2022, 3, 31), '2022-04 Rent'),
            tx_amortized(datetime.date(2022, 4, 1), '2022-04 Rent Amortized(1/12)'),
            tx_amortized(datetime.date(2022, 5, 1), '2022-04 Rent Amortized(2/12)'),
            tx_amortized(datetime.date(2022, 6, 1), '2022-04 Rent Amortized(3/12)'),
            tx_amortized(datetime.date(2022, 7, 1), '2022-04 Rent Amortized(4/12)'),
            tx_amortized(datetime.date(2022, 8, 1), '2022-04 Rent Amortized(5/12)'),
            tx_amortized(datetime.date(2022, 9, 1), '2022-04 Rent Amortized(6/12)'),
            tx_amortized(datetime.date(2022, 10, 1), '2022-04 Rent Amortized(7/12)'),
        ]

        same, missing1, missing2 = compare_entries(list(tests.util.get_transactions_cleaned(entries)), expected_entries)
        self.assertTrue(same)

    def test_amortize_from_custom_account(self):
        journal_str = """
plugin "beancount_periodic.amortize"
1900-01-01 open Liabilities:CreditCard:0001 USD
1900-01-01 open Expenses:Insurance USD
1900-01-01 open Assets:Prepaid:Insurance USD
2026-01-01 * "Insurance Co" "Annual Insurance Premium"
  Liabilities:CreditCard:0001    -1200 USD
  Expenses:Insurance              1200 USD
    amortize: "12 Months / Monthly"
    amortize_from: "Assets:Prepaid:Insurance"
"""
        entries, errors, options_map = load_string(journal_str)
        self.assertEqual(len(errors), 0)

        expected_entries = [
            tx_prepaid(datetime.date(2026, 1, 1), 'Annual Insurance Premium'),
            tx_amortized_prepaid(datetime.date(2026, 1, 1), 'Annual Insurance Premium Amortized(1/12)'),
            tx_amortized_prepaid(datetime.date(2026, 2, 1), 'Annual Insurance Premium Amortized(2/12)'),
            tx_amortized_prepaid(datetime.date(2026, 3, 1), 'Annual Insurance Premium Amortized(3/12)'),
            tx_amortized_prepaid(datetime.date(2026, 4, 1), 'Annual Insurance Premium Amortized(4/12)'),
            tx_amortized_prepaid(datetime.date(2026, 5, 1), 'Annual Insurance Premium Amortized(5/12)'),
            tx_amortized_prepaid(datetime.date(2026, 6, 1), 'Annual Insurance Premium Amortized(6/12)'),
            tx_amortized_prepaid(datetime.date(2026, 7, 1), 'Annual Insurance Premium Amortized(7/12)'),
            tx_amortized_prepaid(datetime.date(2026, 8, 1), 'Annual Insurance Premium Amortized(8/12)'),
            tx_amortized_prepaid(datetime.date(2026, 9, 1), 'Annual Insurance Premium Amortized(9/12)'),
            tx_amortized_prepaid(datetime.date(2026, 10, 1), 'Annual Insurance Premium Amortized(10/12)'),
            tx_amortized_prepaid(datetime.date(2026, 11, 1), 'Annual Insurance Premium Amortized(11/12)'),
            tx_amortized_prepaid(datetime.date(2026, 12, 1), 'Annual Insurance Premium Amortized(12/12)'),
        ]

        same, missing1, missing2 = compare_entries(list(tests.util.get_transactions_cleaned(entries)), expected_entries)
        self.assertTrue(same)

    def test_amortize_from_backward_compatibility(self):
        journal_str = """
plugin "beancount_periodic.amortize"
1900-01-01 open Liabilities:CreditCard:0001 USD
1900-01-01 open Expenses:Insurance USD
1900-01-01 open Equity:Amortization:Insurance USD
2026-01-01 * "Insurance Co" "Annual Insurance Premium"
  Liabilities:CreditCard:0001    -1200 USD
  Expenses:Insurance              1200 USD
    amortize: "12 Months / Monthly"
"""
        entries, errors, options_map = load_string(journal_str)
        self.assertEqual(len(errors), 0)

        expected_original_tx = tests.util.make_transaction(
            date=datetime.date(2026, 1, 1),
            payee='Insurance Co',
            narration='Annual Insurance Premium',
            account_from='Liabilities:CreditCard:0001',
            account_to='Equity:Amortization:Insurance',
            amount='1200',
        )

        expected_amortized_txs = []
        for month in range(1, 13):
            expected_amortized_txs.append(tests.util.make_transaction(
                date=datetime.date(2026, month, 1),
                payee='Insurance Co',
                narration=f'Annual Insurance Premium Amortized({month}/12)',
                account_from='Equity:Amortization:Insurance',
                account_to='Expenses:Insurance',
                amount='100',
            ))

        expected_entries = [expected_original_tx] + expected_amortized_txs

        same, missing1, missing2 = compare_entries(list(tests.util.get_transactions_cleaned(entries)), expected_entries)
        self.assertTrue(same)

    def test_amortize_from_with_income(self):
        journal_str = """
plugin "beancount_periodic.amortize"
1900-01-01 open Assets:Bank USD
1900-01-01 open Income:Consulting USD
1900-01-01 open Liabilities:DeferredRevenue USD
2026-01-01 * "Client" "Annual Consulting Contract"
  Assets:Bank                     12000 USD
  Income:Consulting              -12000 USD
    amortize: "12 Months / Monthly"
    amortize_from: "Liabilities:DeferredRevenue"
"""
        entries, errors, options_map = load_string(journal_str)
        self.assertEqual(len(errors), 0)

        expected_original_tx = tests.util.make_transaction(
            date=datetime.date(2026, 1, 1),
            payee='Client',
            narration='Annual Consulting Contract',
            account_from='Liabilities:DeferredRevenue',
            account_to='Assets:Bank',
            amount='12000',
        )

        expected_amortized_txs = []
        for month in range(1, 13):
            expected_amortized_txs.append(tests.util.make_transaction(
                date=datetime.date(2026, month, 1),
                payee='Client',
                narration=f'Annual Consulting Contract Amortized({month}/12)',
                account_from='Income:Consulting',
                account_to='Liabilities:DeferredRevenue',
                amount='1000',
            ))

        expected_entries = [expected_original_tx] + expected_amortized_txs

        same, missing1, missing2 = compare_entries(list(tests.util.get_transactions_cleaned(entries)), expected_entries)
        self.assertTrue(same)

    def test_amortize_from_multiple_postings(self):
        journal_str = """
plugin "beancount_periodic.amortize"
1900-01-01 open Assets:Bank USD
1900-01-01 open Expenses:Insurance USD
1900-01-01 open Expenses:Subscription USD
1900-01-01 open Assets:Prepaid:Insurance USD
1900-01-01 open Equity:Amortization:Subscription USD
2026-01-01 * "Vendor" "Annual Payments"
  Assets:Bank                    -2400 USD
  Expenses:Insurance              1200 USD
    amortize: "12 Months / Monthly"
    amortize_from: "Assets:Prepaid:Insurance"
  Expenses:Subscription           1200 USD
    amortize: "12 Months / Monthly"
"""
        entries, errors, options_map = load_string(journal_str)
        self.assertEqual(len(errors), 0)

        # The original transaction should have mixed intermediate accounts
        # Insurance -> Assets:Prepaid:Insurance (custom)
        # Subscription -> Equity:Amortization:Subscription (default)
        # Since both postings have the same schedule, they're grouped into combined transactions:
        # 1 original + 12 combined monthly = 13 total

        transactions = list(tests.util.get_transactions_cleaned(entries))
        self.assertEqual(len(transactions), 13)

        # Verify the original transaction uses both intermediate accounts
        original_tx = transactions[0]
        self.assertEqual(original_tx.date, datetime.date(2026, 1, 1))
        account_names = [p.account for p in original_tx.postings]
        self.assertIn('Assets:Bank', account_names)
        self.assertIn('Assets:Prepaid:Insurance', account_names)
        self.assertIn('Equity:Amortization:Subscription', account_names)

        # Verify each amortization transaction has postings from both accounts
        for i in range(1, 13):
            amortized_tx = transactions[i]
            account_names = [p.account for p in amortized_tx.postings]
            self.assertIn('Assets:Prepaid:Insurance', account_names)
            self.assertIn('Expenses:Insurance', account_names)
            self.assertIn('Equity:Amortization:Subscription', account_names)
            self.assertIn('Expenses:Subscription', account_names)

    def test_amortize_label_custom(self):
        journal_str = """
plugin "beancount_periodic.amortize"
1900-01-01 open Liabilities:CreditCard:0001 USD
1900-01-01 open Expenses:Insurance USD
1900-01-01 open Equity:Amortization:Insurance USD
2026-01-01 * "Insurance Co" "Annual Insurance Premium"
  Liabilities:CreditCard:0001    -1200 USD
  Expenses:Insurance              1200 USD
    amortize: "12 Months / Monthly"
    amortize_label: "Prepaid"
"""
        entries, errors, options_map = load_string(journal_str)
        self.assertEqual(len(errors), 0)

        # Verify the narration uses "Prepaid" instead of "Amortized"
        transactions = list(tests.util.get_transactions_cleaned(entries))
        self.assertEqual(len(transactions), 13)  # 1 original + 12 monthly

        for i in range(1, 13):
            amortized_tx = transactions[i]
            self.assertIn(f'Prepaid({i}/12)', amortized_tx.narration)

    def test_amortize_label_with_amortize_from(self):
        journal_str = """
plugin "beancount_periodic.amortize"
1900-01-01 open Liabilities:CreditCard:0001 USD
1900-01-01 open Expenses:Insurance USD
1900-01-01 open Assets:Prepaid:Insurance USD
2026-01-01 * "Insurance Co" "Annual Insurance Premium"
  Liabilities:CreditCard:0001    -1200 USD
  Expenses:Insurance              1200 USD
    amortize: "12 Months / Monthly"
    amortize_from: "Assets:Prepaid:Insurance"
    amortize_label: "Prepaid"
"""
        entries, errors, options_map = load_string(journal_str)
        self.assertEqual(len(errors), 0)

        expected_entries = [
            tx_prepaid(datetime.date(2026, 1, 1), 'Annual Insurance Premium'),
            tx_amortized_prepaid(datetime.date(2026, 1, 1), 'Annual Insurance Premium Prepaid(1/12)'),
            tx_amortized_prepaid(datetime.date(2026, 2, 1), 'Annual Insurance Premium Prepaid(2/12)'),
            tx_amortized_prepaid(datetime.date(2026, 3, 1), 'Annual Insurance Premium Prepaid(3/12)'),
            tx_amortized_prepaid(datetime.date(2026, 4, 1), 'Annual Insurance Premium Prepaid(4/12)'),
            tx_amortized_prepaid(datetime.date(2026, 5, 1), 'Annual Insurance Premium Prepaid(5/12)'),
            tx_amortized_prepaid(datetime.date(2026, 6, 1), 'Annual Insurance Premium Prepaid(6/12)'),
            tx_amortized_prepaid(datetime.date(2026, 7, 1), 'Annual Insurance Premium Prepaid(7/12)'),
            tx_amortized_prepaid(datetime.date(2026, 8, 1), 'Annual Insurance Premium Prepaid(8/12)'),
            tx_amortized_prepaid(datetime.date(2026, 9, 1), 'Annual Insurance Premium Prepaid(9/12)'),
            tx_amortized_prepaid(datetime.date(2026, 10, 1), 'Annual Insurance Premium Prepaid(10/12)'),
            tx_amortized_prepaid(datetime.date(2026, 11, 1), 'Annual Insurance Premium Prepaid(11/12)'),
            tx_amortized_prepaid(datetime.date(2026, 12, 1), 'Annual Insurance Premium Prepaid(12/12)'),
        ]

        same, missing1, missing2 = compare_entries(list(tests.util.get_transactions_cleaned(entries)), expected_entries)
        self.assertTrue(same)

    def test_amortize_label_multiple_same(self):
        journal_str = """
plugin "beancount_periodic.amortize"
1900-01-01 open Assets:Bank USD
1900-01-01 open Expenses:Insurance USD
1900-01-01 open Expenses:Subscription USD
1900-01-01 open Assets:Prepaid:Insurance USD
1900-01-01 open Assets:Prepaid:Subscription USD
2026-01-01 * "Vendor" "Annual Payments"
  Assets:Bank                    -2400 USD
  Expenses:Insurance              1200 USD
    amortize: "12 Months / Monthly"
    amortize_from: "Assets:Prepaid:Insurance"
    amortize_label: "Prepaid"
  Expenses:Subscription           1200 USD
    amortize: "12 Months / Monthly"
    amortize_from: "Assets:Prepaid:Subscription"
    amortize_label: "Prepaid"
"""
        entries, errors, options_map = load_string(journal_str)
        self.assertEqual(len(errors), 0)

        # Both postings have same label, should use "Prepaid"
        transactions = list(tests.util.get_transactions_cleaned(entries))
        self.assertEqual(len(transactions), 13)  # 1 original + 12 monthly

        for i in range(1, 13):
            amortized_tx = transactions[i]
            self.assertIn(f'Prepaid({i}/12)', amortized_tx.narration)

    def test_amortize_label_multiple_different(self):
        journal_str = """
plugin "beancount_periodic.amortize"
1900-01-01 open Assets:Bank USD
1900-01-01 open Expenses:Insurance USD
1900-01-01 open Expenses:Subscription USD
1900-01-01 open Assets:Prepaid:Insurance USD
1900-01-01 open Assets:Prepaid:Subscription USD
2026-01-01 * "Vendor" "Annual Payments"
  Assets:Bank                    -2400 USD
  Expenses:Insurance              1200 USD
    amortize: "12 Months / Monthly"
    amortize_from: "Assets:Prepaid:Insurance"
    amortize_label: "Prepaid"
  Expenses:Subscription           1200 USD
    amortize: "12 Months / Monthly"
    amortize_from: "Assets:Prepaid:Subscription"
    amortize_label: "Deferred"
"""
        entries, errors, options_map = load_string(journal_str)
        self.assertEqual(len(errors), 0)

        # Different labels, should default to "Amortized"
        transactions = list(tests.util.get_transactions_cleaned(entries))
        self.assertEqual(len(transactions), 13)  # 1 original + 12 monthly

        for i in range(1, 13):
            amortized_tx = transactions[i]
            self.assertIn(f'Amortized({i}/12)', amortized_tx.narration)

    def test_amortize_label_backward_compatibility(self):
        journal_str = """
plugin "beancount_periodic.amortize"
1900-01-01 open Liabilities:CreditCard:0001 USD
1900-01-01 open Expenses:Insurance USD
1900-01-01 open Equity:Amortization:Insurance USD
2026-01-01 * "Insurance Co" "Annual Insurance Premium"
  Liabilities:CreditCard:0001    -1200 USD
  Expenses:Insurance              1200 USD
    amortize: "12 Months / Monthly"
"""
        entries, errors, options_map = load_string(journal_str)
        self.assertEqual(len(errors), 0)

        # Without amortize_label, should default to "Amortized"
        transactions = list(tests.util.get_transactions_cleaned(entries))
        self.assertEqual(len(transactions), 13)  # 1 original + 12 monthly

        for i in range(1, 13):
            amortized_tx = transactions[i]
            self.assertIn(f'Amortized({i}/12)', amortized_tx.narration)


if __name__ == '__main__':
    unittest.main()
