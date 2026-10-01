# Excel ideas

The CSV outputs are easy to open directly in Excel.

## PivotTable

Use `daily_metrics.csv` and build a PivotTable with:

- Rows: Region
- Columns: User Profile
- Values: Sum of Incoming Requests, Sum of Completed Requests, Average of SLA Rate

This gives a quick view of workload and service performance by part of the operation.

## Staffing gap formula

If forecast demand is in `B2`, expected requests per person is in `C2`, and current staff is in `D2`:

```excel
=ROUNDUP(B2/(C2*0.85),0)-D2
```

The `0.85` keeps the staffing plan from assuming everyone can run at full capacity all day.

## XLOOKUP example

If each user profile has a different productivity assumption stored in a small lookup table:

```excel
=XLOOKUP(A2,CapacityTable[User Profile],CapacityTable[Requests Per Staff])
```

## Simple status formula

```excel
=IF(E2>0,"Needs Staff",IF(E2<0,"Extra Capacity","Balanced"))
```

I would use conditional formatting on that column so staffing problems stand out without needing to read every row.
