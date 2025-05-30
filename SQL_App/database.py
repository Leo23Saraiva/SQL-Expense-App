# database.py

from PyQt6.QtSql import QSqlDatabase, QSqlQuery


def init_db(db_name):
    database = QSqlDatabase.addDatabase("QSQLITE")
    database.setDatabaseName(db_name)
    if not database.open():
        return False

    query = QSqlQuery()
    query.exec("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT,
            marca TEXT,
            isv REAL,
            nRegistoContabilidade REAL,
            dataCompra TEXT,
            docCompra TEXT,
            tipoDocumento TEXT,
            valorCompra REAL,
            dataVenda TEXT,
            docVenda TEXT,
            valorVenda REAL,
            imposto TEXT,
            taxa TEXT
     )
    """)
    return True


def fetch_expenses():
    query = QSqlQuery(
        "SELECT id, matricula, marca, valorCompra, docVenda, valorVenda, imposto "
        "FROM vehicles"
    )
    vehicles = []
    while query.next():
        vehicles.append([query.value(i) for i in range(7)])  # Now 7 columns
    return vehicles


def add_expense_to_db(
        matricula, marca, isv, nRegistoContabilidade, dataCompra, docCompra, tipoDocumento,
        valorCompra, dataVenda, docVenda, valorVenda, imposto, taxa
):
    query = QSqlQuery()
    query.prepare(
        "INSERT INTO vehicles "
        "(matricula, marca, isv, nRegistoContabilidade, dataCompra, docCompra, tipoDocumento, "
        "valorCompra, dataVenda, docVenda, valorVenda, imposto, taxa) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    query.addBindValue(matricula)
    query.addBindValue(marca)
    query.addBindValue(isv)
    query.addBindValue(nRegistoContabilidade)
    query.addBindValue(dataCompra)
    query.addBindValue(docCompra)
    query.addBindValue(tipoDocumento)
    query.addBindValue(valorCompra)
    query.addBindValue(dataVenda)
    query.addBindValue(docVenda)
    query.addBindValue(valorVenda)
    query.addBindValue(imposto)
    query.addBindValue(taxa)

    print("Prepared Query:", query.lastQuery())
    print("Bound values:")
    print(f"1. matricula: {matricula}")
    print(f"2. marca: {marca}")
    print(f"3. isv: {isv}")
    print(f"4. nRegistoContabilidade: {nRegistoContabilidade}")
    print(f"5. dataCompra: {dataCompra}")
    print(f"6. docCompra: {docCompra}")
    print(f"7. tipoDocumento: {tipoDocumento}")
    print(f"8. valorCompra: {valorCompra}")
    print(f"9. dataVenda: {dataVenda}")
    print(f"10. docVenda: {docVenda}")
    print(f"11. valorVenda: {valorVenda}")
    print(f"12. imposto: {imposto}")
    print(f"13. taxa: {taxa}")

    if not query.exec():
        print("SQL Error:", query.lastError().text())
        return False

    return True


def delete_expense_from_db(expense_id):
    query = QSqlQuery()
    query.prepare("DELETE FROM vehicles WHERE id = ?")
    query.addBindValue(expense_id)
    return query.exec()
