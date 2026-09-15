"""Ligacao medida entre o indice da tabela do `.pds` e o nome do canal (issue #54).

O indice da tabela de blocos segue a ordem de aquisicao do logger, nao o campo de
indice do dicionario. Cada assinatura (o conjunto de nomes do dicionario) ganha
uma tupla: a posicao e o indice da tabela, o valor e o nome do canal, ou `None`
quando o bloco nao tem ancora medida.

Metodo (2026-09-15, `docs/pi-pds-medicao.md`, secao "Ligacao indice -> nome"):
cada bloco de 8 bytes lido como `float64` foi correlacionado com todo canal de
mesma contagem do `.dat` exportado pelo Pi Toolbox da mesma sessao; entra o nome
com |r| > 0,999 e sem conflito entre sessoes. Fica `None` o bloco constante em
todas as sessoes medidas e o nome casado com dois blocos de dado identico
(`Cumulative Time`), porque a correlacao nao separa os dois.

Gerado a partir da medicao; nao editar a mao sem medir de novo.
"""

from __future__ import annotations

LIGACAO_MEDIDA: dict[frozenset[str], tuple[str | None, ...]] = {
    # 46 canais no dicionario; medida em 9 sessoes:
    # P.Piquet000001, P.Piquet000974, P.Piquet000975, P.Piquet000976, P.Piquet000977, P.Piquet000978, P.Piquet000979, P.Piquet000980, P.Piquet000981.
    frozenset(
        (
            "Acc Lat",
            "Acc Long",
            "Air Temp",
            "Alarm Status",
            "Battery Voltage",
            "Beacon Code",
            "Box Temperature",
            "Box Voltage",
            "Brake Press F",
            "Brake Press R",
            "CPU Usage",
            "Can Rx Packets",
            "Cumulative Diff",
            "Cumulative Time",
            "Damper FL",
            "Damper FR",
            "Damper RL",
            "Damper RR",
            "Distance",
            "Elapsed Time",
            "Fuel Economy",
            "Fuel Pressure",
            "Gear",
            "Gear Pot",
            "Lambda",
            "Lap Number",
            "Laps Left",
            "Map",
            "Max Straight Speed",
            "Min Corner Speed",
            "Oil Pressure",
            "Oil Pressure Pi",
            "Oil Temp",
            "RPM",
            "Running Lap Time",
            "Section Diff",
            "Section Time",
            "Speed",
            "Speed ECU",
            "Steering",
            "Tank Fuel",
            "Tank Fuel Used",
            "Throttle Position",
            "WS_FL",
            "WS_FR",
            "Water Temp",
        )
    ): (
        "Steering",  # 0
        "Damper FR",  # 1
        "Damper FL",  # 2
        "Damper RR",  # 3
        "Damper RL",  # 4
        "Gear Pot",  # 5
        "WS_FL",  # 6
        "WS_FR",  # 7
        "Speed",  # 8
        "Min Corner Speed",  # 9
        "Max Straight Speed",  # 10
        "Beacon Code",  # 11
        "Distance",  # 12
        "Acc Lat",  # 13
        "Acc Long",  # 14
        "Brake Press F",  # 15
        "Brake Press R",  # 16
        "RPM",  # 17
        None,  # 18
        "Throttle Position",  # 19
        "Battery Voltage",  # 20
        "Lambda",  # 21
        None,  # 22
        None,  # 23
        "Air Temp",  # 24
        "Oil Pressure Pi",  # 25
        "Water Temp",  # 26
        None,  # 27
        "Section Diff",  # 28
        "Elapsed Time",  # 29
        "Box Voltage",  # 30
        "Box Temperature",  # 31
        "Oil Temp",  # 32
        "CPU Usage",  # 33
        "Lap Number",  # 34
        "Running Lap Time",  # 35
        None,  # 36
        None,  # 37
        "Alarm Status",  # 38
        None,  # 39
        None,  # 40
        None,  # 41
        None,  # 42
        "Can Rx Packets",  # 43
        None,  # 44
        None,  # 45
    ),
    # 47 canais no dicionario; medida em 12 sessoes:
    # P.Piquet000985, P.Piquet000986, P.Piquet000987, P.Piquet000988, P.Piquet000989, P.Piquet000990, P.Piquet000991, P.Piquet000993, P.Piquet000994, P.Piquet000995, P.Piquet000996, P.Piquet000997.
    frozenset(
        (
            "Acc Lat",
            "Acc Long",
            "Air Temp",
            "Alarm Status",
            "Battery Voltage",
            "Beacon Code",
            "Box Temperature",
            "Box Voltage",
            "Brake Press F",
            "Brake Press R",
            "CPU Usage",
            "Can Rx Packets",
            "Cumulative Diff",
            "Cumulative Time",
            "Damper FL",
            "Damper FR",
            "Damper RL",
            "Damper RR",
            "Distance",
            "Elapsed Time",
            "Fuel Economy",
            "Fuel Pressure",
            "Fuel PressurePi",
            "Gear",
            "Gear Pot",
            "Lambda",
            "Lap Number",
            "Laps Left",
            "Map",
            "Max Straight Speed",
            "Min Corner Speed",
            "Oil Pressure",
            "Oil Pressure Pi",
            "Oil Temp",
            "RPM",
            "Running Lap Time",
            "Section Diff",
            "Section Time",
            "Speed",
            "Speed ECU",
            "Steering",
            "Tank Fuel",
            "Tank Fuel Used",
            "Throttle Position",
            "WS_FL",
            "WS_FR",
            "Water Temp",
        )
    ): (
        "Steering",  # 0
        "Damper FR",  # 1
        "Damper FL",  # 2
        "Damper RR",  # 3
        "Damper RL",  # 4
        "Gear Pot",  # 5
        "WS_FL",  # 6
        "WS_FR",  # 7
        "Speed",  # 8
        "Min Corner Speed",  # 9
        "Max Straight Speed",  # 10
        "Beacon Code",  # 11
        "Distance",  # 12
        "Acc Lat",  # 13
        "Acc Long",  # 14
        "Brake Press F",  # 15
        "Brake Press R",  # 16
        "RPM",  # 17
        None,  # 18
        "Throttle Position",  # 19
        "Battery Voltage",  # 20
        "Lambda",  # 21
        None,  # 22
        None,  # 23
        "Air Temp",  # 24
        "Fuel PressurePi",  # 25
        "Oil Pressure Pi",  # 26
        "Water Temp",  # 27
        None,  # 28
        "Section Diff",  # 29
        "Elapsed Time",  # 30
        "Box Voltage",  # 31
        "Box Temperature",  # 32
        "Oil Temp",  # 33
        "CPU Usage",  # 34
        "Lap Number",  # 35
        "Running Lap Time",  # 36
        None,  # 37
        None,  # 38
        "Alarm Status",  # 39
        None,  # 40
        None,  # 41
        None,  # 42
        None,  # 43
        "Can Rx Packets",  # 44
        None,  # 45
        None,  # 46
    ),
}
