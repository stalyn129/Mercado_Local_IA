class DemandModel:
    def predecir(self, historico_ventas):
        # Analiza la columna 'cantidad' de tu tabla 'detalles_pedido'
        if sum(historico_ventas) > 100:
            return "ALTA"
        return "ESTABLE"