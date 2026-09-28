def calculate_bill(rent, rate, units):
    electricity = units * rate
    total = rent + electricity

    return {
        "rent": rent,
        "electricity": electricity,
        "total": total
    }
