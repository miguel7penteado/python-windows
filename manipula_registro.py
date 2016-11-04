"""
Mostra/Modifica/Insere variaveis-ambiente no registro (exemplo `PATH`) e notifica aplicacoes windows para aplicar mudancas.

Primeiro procura mostrar/modificar HKEY_LOCAL_MACHINE (todos usuarios), 
e, se nao acessivel devido falta de permissoes administrativas, recorre
a HKEY_CURRENT_USER.
Operacoes de escrever e apagar para se executam na arvore do usuario
se as operacoes funcionarem na arvore de todos os usuarios.

Sintaxe: 
    {prog}                  : Imprime todas as variaveis de ambiente. 
    {prog}  VARIAVEL        : Imprime o VALOR para VARIAVEL. 
    {prog}  VARIAVEL  VALOR : Configura VALOR para VARIAVEL. 
    {prog}  +VARNAME  VALOR : Insere VALOR em VARIAVEL delimitadado 
			por ';' (exemplo: como usado no `PATH`). 
    
    {prog}  -VARIAVEL       : apaga VARIAVEL. 

Note que a janela de comando atual nao sera afetada.
Mudancas vao acontecer apenas em novas janelas do DOS.
"""

import winreg
import os, sys, win32gui, win32con

def chave_registro(arvore, caminho, nome_variavel):
    return '%s\%s:%s' % (arvore, caminho, nome_variavel) 

def entrada_registro(arvore, caminho, nome_variavel, valor):
    return '%s=%s' % (chave_registro(arvore, caminho, nome_variavel), valor)

def pesquisa_registro(chave, nome_variavel):
    valor, id_tipo = winreg.QueryValueEx(chave, nome_variavel)
    return valor

def gera_todas_entradas(arvore, caminho, chave):
    contador = 0
    while True:
        try:
            no,valor,tipo = winreg.EnumValue(chave, contador)
            yield entrada_registro(arvore, caminho, no, valor)
            contador += 1
        except OSError:
            break ## Esperado, eh como a interacao termina.

def notificar_windows(acao, arvore, caminho, nome_variavel, parametro_valor):
    win32gui.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment')
    print("---%s %s" % (acao, entrada_registro(arvore, caminho, nome_variavel, parametro_valor)), file=sys.stderr)

def manipula_variaveis_ambiente_registro(nome_variavel=None, parametro_valor=None):
    chaves_registro = [
        ('HKEY_LOCAL_MACHINE', r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'),
        ('HKEY_CURRENT_USER', r'Environment'),
    ]
    for (nome_arvore, caminho) in chaves_registro:
        arvore = eval('winreg.%s'%nome_arvore)
        try:
            with winreg.ConnectRegistry(None, arvore) as registro:
                with winreg.OpenKey(registro, caminho, 0, winreg.KEY_ALL_ACCESS) as chave:
                    if not nome_variavel:
                        for entidade in gera_todas_entradas(nome_arvore, caminho, chave):
                            print(entidade)
                    else:
                        if not parametro_valor:
                            if nome_variavel.startswith('-'):
                                nome_variavel = nome_variavel[1:]
                                parametro_valor = pesquisa_registro(chave, nome_variavel)
                                winreg.DeleteValue(chave, nome_variavel)
                                notificar_windows("Apagado", nome_arvore, caminho, nome_variavel, parametro_valor)
                                break  ## Nao propagar dentro da arvore do usuario.
                            else:
                                parametro_valor = pesquisa_registro(chave, nome_variavel)
                                print(entrada_registro(nome_arvore, caminho, nome_variavel, parametro_valor))
                        else:
                            if nome_variavel.startswith('+'):
                                nome_variavel = nome_variavel[1:]
                                parametro_valor = pesquisa_registro(chave, nome_variavel) + ';' + parametro_valor
                            winreg.SetValueEx(chave, nome_variavel, 0, winreg.REG_EXPAND_SZ, parametro_valor)
                            notificar_windows("Atualizado", nome_arvore, caminho, nome_variavel, parametro_valor)
                            break  ## Nao propagar dentro da arvore do usuario.
        except PermissionError as erro:
            print("!!!Nao pude acessar %s devido a: %s" % 
                    (chave_registro(nome_arvore, caminho, nome_variavel), erro), file=sys.stderr)
        except FileNotFoundError as erro:
            print("!!!Nao pude encontrar %s devido a: %s" % 
                    (chave_registro(nome_arvore, caminho, nome_variavel), erro), file=sys.stderr)

if __name__=='__main__':
    argumentos = sys.argv
    numero_argumentos = len(argumentos)
    if numero_argumentos > 3:
        print(__doc__.format(prog=argumentos[0]), file=sys.stderr)
        sys.exit()

    manipula_variaveis_ambiente_registro(*argumentos[1:])
