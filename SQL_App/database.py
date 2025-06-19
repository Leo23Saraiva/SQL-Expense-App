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
            valorBase REAL,  -- COLUNA 'valorBase' AQUI
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
            numeroQuadro = :numeroQuadro,
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

    # Certifique-se de que os valores 'None' são tratados como QVariant() nulo
    for key, value in data.items():
        if value is None:
            query.bindValue(f":{key}", None)  # QVariant() para NULL
        else:
            query.bindValue(f":{key}", value)
    query.bindValue(":id", id)

    if not query.exec():
        print(f"Erro ao atualizar registo: {query.lastError().text()}")
        return False
    return True


def add_expense_to_db(matricula, marca, numeroQuadro, isv, nRegistoContabilidade,
                      dataCompra, docCompra, tipoDocumento, valorCompra,
                      dataVenda, docVenda, valorVenda, imposto, valorBase, taxa, regime_fiscal):
    query = QSqlQuery()
    query.prepare("""
        INSERT INTO vehicles (matricula, marca, numeroQuadro, isv, nRegistoContabilidade,
                              dataCompra, docCompra, tipoDocumento, valorCompra,
                              dataVenda, docVenda, valorVenda, imposto, valorBase, taxa, regime_fiscal)
        VALUES (:matricula, :marca, :numeroQuadro, :isv, :nRegistoContabilidade,
                :dataCompra, :docCompra, :tipoDocumento, :valorCompra,
                :dataVenda, :docVenda, :valorVenda, :imposto, :valorBase, :taxa, :regime_fiscal)
    """)
    query.bindValue(":matricula", matricula)
    query.bindValue(":marca", marca)
    query.bindValue(":numeroQuadro", numeroQuadro)
    query.bindValue(":isv", isv)
    query.bindValue(":nRegistoContabilidade", nRegistoContabilidade)
    query.bindValue(":dataCompra", dataCompra)
    query.bindValue(":docCompra", docCompra)
    query.bindValue(":tipoDocumento", tipoDocumento)
    query.bindValue(":valorCompra", valorCompra)
    query.bindValue(":dataVenda", dataVenda)
    query.bindValue(":docVenda", docVenda)
    query.bindValue(":valorVenda", valorVenda)
    query.bindValue(":imposto", imposto)
    query.bindValue(":valorBase", valorBase)
    query.bindValue(":taxa", taxa)
    query.bindValue(":regime_fiscal", regime_fiscal)

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
    # Adicionado dataVenda à query
    query = QSqlQuery(
        "SELECT id, matricula, marca, valorCompra, docVenda, valorVenda, imposto, valorBase, dataVenda FROM vehicles")
    if not query.exec():
        print(f"Erro ao buscar despesas: {query.lastError().text()}")
        return expenses

    while query.next():
        expenses.append([
            query.value(0),  # id
            query.value(1),  # matricula
            query.value(2),  # marca
            query.value(3),  # valorCompra
            query.value(4),  # docVenda
            query.value(5),  # valorVenda
            query.value(6),  # imposto
            query.value(7),  # valorBase
            query.value(8)  # dataVenda (Novo: para lógica de vendido)
        ])
    return expenses


def fetch_vehicle_by_id(vehicle_id):
    query = QSqlQuery()
    query.prepare("SELECT id, matricula, marca, numeroQuadro, isv, nRegistoContabilidade, dataCompra, docCompra, "
                  "tipoDocumento, valorCompra, dataVenda, docVenda, valorVenda, imposto, valorBase, taxa, "
                  "regime_fiscal FROM vehicles WHERE id = :id")
    query.bindValue(":id", vehicle_id)

    if not query.exec():
        print(f"Erro ao buscar veículo por ID: {query.lastError().text()}")
        return None

    if query.next():
        return {
            "id": query.value(0),
            "matricula": query.value(1),
            "marca": query.value(2),
            "numeroQuadro": query.value(3),
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


def fetch_unique_marcas():
    query = QSqlQuery("SELECT DISTINCT marca FROM vehicles ORDER BY marca COLLATE NOCASE")
    marcas = []
    while query.next():
        marca = query.value(0)
        if marca:
            marcas.append(str(marca))
    return marcas


def fetch_unique_matriculas():
    query = QSqlQuery("SELECT DISTINCT matricula FROM vehicles ORDER BY matricula COLLATE NOCASE")
    matriculas = []
    while query.next():
        matricula = query.value(0)
        if matricula:
            matriculas.append(str(matricula))
    return matriculas
