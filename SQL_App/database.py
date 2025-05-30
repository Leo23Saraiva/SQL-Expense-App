# database.py

from PyQt6.QtSql import QSqlDatabase, QSqlQuery, QSqlError


def init_db(db_name):
    database = QSqlDatabase.addDatabase("QSQLITE")
    database.setDatabaseName(db_name)
    if not database.open():
        print(f"Erro ao abrir a base de dados: {database.lastError().text()}") # Mensagem de erro mais detalhada
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


def update_expense_in_db(id, data: dict):
    query = QSqlQuery()
    query.prepare("""
        UPDATE vehicles SET
            matricula = :matricula,
            marca = :marca,
            isv = :isv,
            nRegistoContabilidade = :nRegistoContabilidade,
            dataCompra = :dataCompra,
            docCompra = :docCompra,
            tipoDocumento = :tipoDocumento,
            valorCompra = :valorCompra,
            dataVenda = :dataVenda,
            docVenda = :docVenda,
            valorVenda = :valorVenda,
            imposto = :imposto,
            taxa = :taxa
        WHERE id = :id
    """)

    # Ligação de parâmetros - As chaves do dicionário 'data' DEVEM corresponder aos placeholders
    query.bindValue(":matricula", data.get("matricula"))
    query.bindValue(":marca", data.get("marca"))
    query.bindValue(":isv", data.get("isv"))
    query.bindValue(":nRegistoContabilidade", data.get("nRegistoContabilidade"))
    query.bindValue(":dataCompra", data.get("dataCompra"))
    query.bindValue(":docCompra", data.get("docCompra"))
    query.bindValue(":tipoDocumento", data.get("tipoDocumento"))
    query.bindValue(":valorCompra", data.get("valorCompra"))
    query.bindValue(":dataVenda", data.get("dataVenda"))
    query.bindValue(":docVenda", data.get("docVenda"))
    query.bindValue(":valorVenda", data.get("valorVenda"))
    query.bindValue(":imposto", data.get("imposto"))
    query.bindValue(":taxa", data.get("taxa"))
    query.bindValue(":id", id)

    if not query.exec():
        print("Valores vinculados:", query.boundValues())
        print("Erro ao atualizar (SQL Error):", query.lastError().text())
        return False

    return True


def fetch_vehicle_by_id(vehicle_id):
    query = QSqlQuery()
    query.prepare("SELECT * FROM vehicles WHERE id = ?")
    query.addBindValue(vehicle_id)
    if query.exec() and query.next():
        # Map column names to values
        vehicle_data = {
            "id": query.value("id"),
            "matricula": query.value("matricula"),
            "marca": query.value("marca"),
            "isv": query.value("isv"),
            "nRegistoContabilidade": query.value("nRegistoContabilidade"),
            "dataCompra": query.value("dataCompra"),
            "docCompra": query.value("docCompra"),
            "tipoDocumento": query.value("tipoDocumento"),
            "valorCompra": query.value("valorCompra"),
            "dataVenda": query.value("dataVenda"),
            "docVenda": query.value("docVenda"),
            "valorVenda": query.value("valorVenda"),
            "imposto": query.value("imposto"),
            "taxa": query.value("taxa"),
        }
        return vehicle_data
    return None


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
