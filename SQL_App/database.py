# database.py

from PyQt6.QtSql import QSqlDatabase, QSqlQuery, QSqlError


def init_db(db_name):
    database = QSqlDatabase.addDatabase("QSQLITE")
    database.setDatabaseName(db_name)
    if not database.open():
        print(f"Erro ao abrir a base de dados: {database.lastError().text()}")
        return False

    query = QSqlQuery()
    # CERTIFIQUE-SE QUE ESTA ESTRUTURA DA TABELA TEM 'valorBase REAL'
    query.exec("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT,
            marca TEXT,
            numeroQuadro TEXT,  -- NOVO CAMPO: NUMERO DE QUADRO
            isv REAL,
            nRegistoContabilidade TEXT,
            dataCompra TEXT,
            docCompra TEXT,
            tipoDocumento TEXT,
            valorCompra REAL,
            dataVenda TEXT,
            docVenda TEXT,
            valorVenda REAL,
            imposto REAL,
            valorBase REAL,
            taxa REAL,
            regime_fiscal TEXT
        )
    """)
    if query.lastError().isValid():
        print(f"Erro na criação da tabela: {query.lastError().text()}")
        return False
    return True


def update_expense_in_db(id, data: dict):
    query = QSqlQuery()
    query.prepare("""
        UPDATE vehicles SET
            matricula = :matricula,
            marca = :marca,
            numeroQuadro = :numeroQuadro,  -- NOVO CAMPO NO UPDATE
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
            valorBase = :valorBase,
            taxa = :taxa,
            regime_fiscal = :regime_fiscal
        WHERE id = :id
    """)
    query.bindValue(":id", id)
    query.bindValue(":matricula", data.get("matricula"))
    query.bindValue(":marca", data.get("marca"))
    query.bindValue(":numeroQuadro", data.get("numeroQuadro"))  # BIND DO NOVO CAMPO
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
    query.bindValue(":valorBase", data.get("valorBase"))
    query.bindValue(":taxa", data.get("taxa"))
    query.bindValue(":regime_fiscal", data.get("regime_fiscal"))

    if not query.exec():
        print(f"Erro ao atualizar registo: {query.lastError().text()}")
        return False
    return True


def add_expense_to_db(matricula, marca, numeroQuadro, isv, nRegistoContabilidade, dataCompra, docCompra, # NOVO CAMPO NO ADD
                      tipoDocumento, valorCompra, dataVenda, docVenda, valorVenda, imposto, valorBase, taxa, regime_fiscal):
    query = QSqlQuery()
    query.prepare(
        "INSERT INTO vehicles (matricula, marca, numeroQuadro, isv, nRegistoContabilidade, dataCompra, docCompra, " # NOVO CAMPO NO INSERT
        "tipoDocumento, valorCompra, dataVenda, docVenda, valorVenda, imposto, valorBase, taxa, regime_fiscal) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)" # Um novo '?' para o novo campo
    )
    query.addBindValue(matricula)
    query.addBindValue(marca)
    query.addBindValue(numeroQuadro) # BIND DO NOVO CAMPO
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
    query.addBindValue(valorBase)
    query.addBindValue(taxa)
    query.addBindValue(regime_fiscal)

    print("Prepared Query:", query.lastQuery())
    print("Bound values:")
    print(f"1. matricula: {matricula}")
    print(f"2. marca: {marca}")
    print(f"3. numeroQuadro: {numeroQuadro}") # Verificação no print
    print(f"4. isv: {isv}")
    print(f"5. nRegistoContabilidade: {nRegistoContabilidade}")
    print(f"6. dataCompra: {dataCompra}")
    print(f"7. docCompra: {docCompra}")
    print(f"8. tipoDocumento: {tipoDocumento}")
    print(f"9. valorCompra: {valorCompra}")
    print(f"10. dataVenda: {dataVenda}")
    print(f"11. docVenda: {docVenda}")
    print(f"12. valorVenda: {valorVenda}")
    print(f"13. imposto: {imposto}")
    print(f"14. valorBase: {valorBase}")
    print(f"15. taxa: {taxa}")
    print(f"16. regime_fiscal: {regime_fiscal}")

    if not query.exec():
        print(f"Erro ao adicionar registo: {query.lastError().text()}")
        return False
    return True


def delete_expense_from_db(id):
    query = QSqlQuery()
    query.prepare("DELETE FROM vehicles WHERE id = :id")
    query.bindValue(":id", id)
    if not query.exec():
        print(f"Erro ao eliminar registo: {query.lastError().text()}")
        return False
    return True


def fetch_expenses():
    expenses = []
    # A Taxa e o valorBase não estão incluídos para a tabela principal
    query = QSqlQuery("SELECT id, matricula, marca, valorCompra, docVenda, valorVenda, imposto FROM vehicles")
    while query.next():
        expenses.append([
            query.value(0),  # id
            query.value(1),  # matricula
            query.value(2),  # marca
            query.value(3),  # valorCompra
            query.value(4),  # docVenda
            query.value(5),  # valorVenda
            query.value(6)   # imposto
        ])
    return expenses

def fetch_vehicle_by_id(vehicle_id):
    query = QSqlQuery()
    query.prepare("SELECT id, matricula, marca, numeroQuadro, isv, nRegistoContabilidade, dataCompra, docCompra, " # NOVO CAMPO NO SELECT
                  "tipoDocumento, valorCompra, dataVenda, docVenda, valorVenda, imposto, valorBase, taxa, regime_fiscal "
                  "FROM vehicles WHERE id = :id")
    query.bindValue(":id", vehicle_id)

    if not query.exec():
        print(f"Erro ao buscar veículo por ID: {query.lastError().text()}")
        return None

    if query.next():
        return {
            "id": query.value(0),
            "matricula": query.value(1),
            "marca": query.value(2),
            "numeroQuadro": query.value(3), # Obtenção do valor da coluna 3 para 'numeroQuadro'
            "isv": query.value(4),
            "nRegistoContabilidade": query.value(5),
            "dataCompra": query.value(6),
            "docCompra": query.value(7),
            "tipoDocumento": query.value(8),
            "valorCompra": query.value(9),
            "dataVenda": query.value(10),
            "docVenda": query.value(11),
            "valorVenda": query.value(12),
            "imposto": query.value(13),
            "valorBase": query.value(14),
            "taxa": query.value(15),
            "regime_fiscal": query.value(16)
        }
    return None