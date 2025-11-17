from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import *
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
import os
import csv

# =====================================================================
# CONFIGURAÇÕES
# =====================================================================
PAUSA_A_CADA = 20
TEMPO_PAUSA = 2
MAX_TENTATIVAS_CLICK = 3
MAX_TENTATIVAS_ENVIO = 3
TIMEOUT_ELEMENTO = 15
TEMPO_ENTRE_DEZENAS = 0.3
VERIFICAR_CARRINHO = True

URL_HOME = "https://www.loteriasonline.caixa.gov.br"
URL_MEGA = "https://www.loteriasonline.caixa.gov.br/silce-web/#/mega-sena/especial"

JOGOS_ENVIADOS = set()   # DETECÇÃO DE REPETIDOS


# =====================================================================
# PASTAS
# =====================================================================
LOG_DIR = "logs"
PRINT_DIR = "prints"
REL_DIR = "relatorios"

for d in [LOG_DIR, PRINT_DIR, REL_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)


# =====================================================================
# ARQUIVOS
# =====================================================================
LOG_FILE = f"{LOG_DIR}/mega_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
RELATORIO = f"{REL_DIR}/mega_resultados_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"


# =====================================================================
# LOG
# =====================================================================
def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] {msg}"
    print(linha)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


# =====================================================================
# PRINT AUTOMÁTICO
# =====================================================================
def salvar_print(driver, titulo):
    nome = f"{PRINT_DIR}/{titulo}_{int(time.time())}.png"
    driver.save_screenshot(nome)
    log(f"📸 Print salvo: {nome}")
    return nome


# =====================================================================
# RELATÓRIO FINAL
# =====================================================================
with open(RELATORIO, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Jogo Nº", "Dezenas", "Status", "Print", "Obs"])


def registrar_resultado(numero, dezenas, status, imagem, obs):
    with open(RELATORIO, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([numero, dezenas, status, imagem, obs])


# =====================================================================
# LEITURA DO CSV
# =====================================================================
def ler_jogos():
    jogos = []
    erros = []
    
    try:
        with open("mega.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # pula cabeçalho
            
            for idx, row in enumerate(reader, start=2):
                if len(row) < 7:
                    erros.append(f"Linha {idx}: dados insuficientes ({len(row)} colunas)")
                    continue
                    
                dezenas = []
                for x in row[1:7]:
                    x = x.strip()
                    if x.isdigit():
                        n = int(x)
                        if 1 <= n <= 60:
                            dezenas.append(n)
                        else:
                            erros.append(f"Linha {idx}: número {n} fora do intervalo (1-60)")
                
                if len(dezenas) == 6:
                    # Verificar duplicatas DENTRO do jogo
                    if len(set(dezenas)) != 6:
                        erros.append(f"Linha {idx}: números duplicados no jogo {dezenas}")
                    else:
                        jogos.append(tuple(sorted(dezenas)))
                else:
                    erros.append(f"Linha {idx}: {len(dezenas)} dezenas encontradas (precisa 6)")
        
        if erros:
            log("⚠ ERROS NO ARQUIVO CSV:")
            for e in erros:
                log(f"  - {e}")
        
        return jogos
        
    except FileNotFoundError:
        log("❌ ERRO: Arquivo mega.csv não encontrado!")
        return []
    except Exception as e:
        log(f"❌ ERRO ao ler CSV: {e}")
        return []


# =====================================================================
# ABERTURA DO SITE
# =====================================================================
def abrir_site():
    log("Abrindo navegador...")
    opts = webdriver.ChromeOptions()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.get(URL_HOME)
    return driver


# =====================================================================
# POPUP SIM
# =====================================================================
def clicar_sim(driver):
    wait = WebDriverWait(driver, 10)
    try:
        sim_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(text(),'Sim')]")
        ))
        driver.execute_script("arguments[0].click();", sim_btn)
        time.sleep(2)
        log("✔ Clique em SIM realizado.")
    except:
        log("ℹ Nenhum popup SIM encontrado.")


# =====================================================================
# FECHAR POPUPS
# =====================================================================
def fechar_popups(driver):
    xpaths = [
        "//button[contains(text(),'Aceitar')]",
        "//button[contains(text(),'Fechar')]",
        "//button[contains(text(),'OK')]",
        "//button[contains(text(),'Confirmar')]",
    ]

    for xp in xpaths:
        try:
            el = driver.find_element(By.XPATH, xp)
            driver.execute_script("arguments[0].click();", el)
            log(f"✔ Popup fechado: {xp}")
            time.sleep(1)
        except:
            pass


# =====================================================================
# LIMPAR VOLANTE
# =====================================================================
def limpar_volante(driver):
    try:
        wait = WebDriverWait(driver, 10)
        bot = wait.until(EC.presence_of_element_located((By.ID, "limparvolante")))
        driver.execute_script("arguments[0].click();", bot)
        time.sleep(0.5)
        log("🧽 Volante limpo com sucesso.")
        return True
    except Exception as e:
        log(f"⚠ Erro ao limpar volante: {e}")
        return False


# =====================================================================
# VERIFICAR SE DEZENA ESTÁ SELECIONADA
# =====================================================================
def verificar_dezena_selecionada(driver, dez):
    """Verifica se dezena está realmente selecionada"""
    try:
        num = f"{dez:02d}"
        el = driver.find_element(By.ID, f"n{num}")
        classes = el.get_attribute("class") or ""
        return "selected" in classes or "active" in classes
    except:
        return False


# =====================================================================
# CLICAR DEZENA
# =====================================================================
def clicar_dezena(driver, dez):
    wait = WebDriverWait(driver, TIMEOUT_ELEMENTO)
    num = f"{dez:02d}"
    element_id = f"n{num}"

    for tentativa in range(1, MAX_TENTATIVAS_CLICK + 1):
        try:
            el = wait.until(EC.presence_of_element_located((By.ID, element_id)))
            
            # Scroll até o elemento
            # driver.execute_script("arguments[0].scrollIntoView(true);", el)
            time.sleep(0.2)
            
            driver.execute_script("arguments[0].click();", el)
            time.sleep(TEMPO_ENTRE_DEZENAS)

            if verificar_dezena_selecionada(driver, dez):
                log(f"✔ Dezena {num} marcada!")
                return True

            log(f"❗ Não marcou {num} (tentativa {tentativa})")

        except Exception as e:
            log(f"⚠ Erro ao clicar {num}: {e}")

    log(f"❌ Falha definitiva ao marcar {num}")
    return False


# =====================================================================
# VERIFICAR JOGO NO CARRINHO
# =====================================================================
def verificar_jogo_no_carrinho(driver):
    """Verifica se o jogo foi realmente adicionado ao carrinho"""
    try:
        wait = WebDriverWait(driver, 5)
        # Tente encontrar elementos que indiquem sucesso
        # Ajuste os seletores conforme a interface real do site
        
        # Opção 1: Verificar mensagem de sucesso
        try:
            mensagem = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'adicionado') or contains(text(),'carrinho')]")
            ))
            log("✔ Confirmação de adição ao carrinho detectada")
            return True
        except:
            pass
        
        # Opção 2: Verificar contador do carrinho
        try:
            contador = driver.find_element(By.CLASS_NAME, "contador-carrinho")
            if contador and contador.text:
                log(f"✔ Contador do carrinho: {contador.text}")
                return True
        except:
            pass
        
        # Opção 3: Verificar se volante foi limpo automaticamente
        try:
            dezenas_selecionadas = driver.find_elements(
                By.CSS_SELECTOR, ".dezena.selected, .numero.selected"
            )
            if len(dezenas_selecionadas) == 0:
                log("✔ Volante limpo após envio (indicação de sucesso)")
                return True
        except:
            pass
        
        return False
        
    except Exception as e:
        log(f"⚠ Erro ao verificar carrinho: {e}")
        return False


# =====================================================================
# MARCAR JOGO
# =====================================================================
def marcar_jogo(driver, dezenas):
    log(f"📌 Lançando jogo: {dezenas}")

    for d in dezenas:
        if not clicar_dezena(driver, d):
            log("🚫 Falha ao marcar o jogo.")
            limpar_volante(driver)
            return False

    log("✔ Todas as dezenas foram marcadas!")
    return True


# =====================================================================
# ENVIAR JOGO AO CARRINHO (MELHORADO)
# =====================================================================
def enviar_jogo(driver):
    for tentativa in range(1, MAX_TENTATIVAS_ENVIO + 1):
        try:
            wait = WebDriverWait(driver, 20)
            bot = wait.until(EC.presence_of_element_located(
                (By.ID, "colocarnocarrinho")
            ))
            
            # Scroll até o botão
            # driver.execute_script("arguments[0].scrollIntoView(true);", bot)
            time.sleep(0.3)
            
            driver.execute_script("arguments[0].click();", bot)
            log(f"✔ Clique no botão 'Colocar no Carrinho' realizado (tentativa {tentativa})")
            time.sleep(2)
            
            # Verificar se foi adicionado
            if VERIFICAR_CARRINHO:
                if verificar_jogo_no_carrinho(driver):
                    log("✅ Jogo confirmado no carrinho!")
                    return True
                else:
                    log(f"⚠ Envio não confirmado (tentativa {tentativa})")
            else:
                log("✔ Jogo enviado (verificação desabilitada)")
                return True
                
        except Exception as e:
            log(f"⚠ Erro ao enviar (tentativa {tentativa}): {e}")
        
        if tentativa < MAX_TENTATIVAS_ENVIO:
            log("⏳ Aguardando antes de tentar novamente...")
            time.sleep(1)
    
    log("❌ Falha ao enviar após todas as tentativas")
    log("🧽 Limpando volante...")
    limpar_volante(driver)
    return False


# =====================================================================
# RECUPERAR DE ERRO
# =====================================================================
def recuperar_de_erro(driver):
    log("🔄 Tentando recuperar de erro...")
    try:
        driver.refresh()
        time.sleep(3)
        fechar_popups(driver)
        limpar_volante(driver)
        log("✔ Recuperação bem-sucedida")
        return True
    except Exception as e:
        log(f"❌ Falha na recuperação: {e}")
        return False


# =====================================================================
# PROCESSO PRINCIPAL
# =====================================================================
def principal():
    driver = None
    sucessos = 0
    erros = 0
    repetidos = 0
    
    try:
        jogos = ler_jogos()
        total = len(jogos)
        
        if total == 0:
            log("❌ Nenhum jogo válido encontrado. Encerrando.")
            return
        
        log(f"\n{'='*60}")
        log(f"🔎 {total} jogos válidos encontrados no arquivo mega.csv")
        log(f"{'='*60}\n")

        driver = abrir_site()
        time.sleep(2)

        clicar_sim(driver)
        fechar_popups(driver)
        
        log("🎯 Navegando para a página da Mega-Sena...")
        driver.get(URL_MEGA)
        time.sleep(3)
        fechar_popups(driver)

        for i, jogo in enumerate(jogos, start=1):
            dezenas = tuple(sorted(jogo))
            
            log(f"\n{'='*60}")
            log(f"🎲 JOGO {i}/{total} ({(i/total)*100:.1f}%)")
            log(f"{'='*60}")

            # DETECÇÃO DE REPETIDOS
            if dezenas in JOGOS_ENVIADOS:
                log(f"⚠ Jogo repetido detectado e pulado: {dezenas}")
                registrar_resultado(i, dezenas, "REPETIDO", "", "Jogo duplicado")
                repetidos += 1
                continue

            img_ini = salvar_print(driver, f"antes_jogo_{i}")

            if not marcar_jogo(driver, dezenas):
                log("🚫 Erro ao marcar dezenas")
                img = salvar_print(driver, f"erro_marcar_{i}")
                registrar_resultado(i, dezenas, "ERRO", img, "Falha ao marcar dezenas")
                erros += 1
                
                # Tentar recuperar
                recuperar_de_erro(driver)
                continue

            img_mar = salvar_print(driver, f"marcado_jogo_{i}")

            if enviar_jogo(driver):
                img_env = salvar_print(driver, f"enviado_{i}")
                registrar_resultado(i, dezenas, "OK", img_env, "Enviado com sucesso")
                JOGOS_ENVIADOS.add(dezenas)
                sucessos += 1
                log("✅ Jogo processado com sucesso!")

            else:
                img = salvar_print(driver, f"erro_envio_{i}")
                registrar_resultado(i, dezenas, "ERRO", img, "Falha ao enviar")
                erros += 1
                
                # Tentar recuperar
                recuperar_de_erro(driver)
                continue

            # Status atual
            log(f"\n📊 STATUS ATUAL:")
            log(f"   ✅ Sucessos: {sucessos}")
            log(f"   ❌ Erros: {erros}")
            log(f"   ⚠ Repetidos: {repetidos}")
            log(f"   📝 Restantes: {total - i}")

            # Pausa automática
            if i % PAUSA_A_CADA == 0 and i < total:
                log(f"\n⏸ Pausa automática de {TEMPO_PAUSA}s")
                time.sleep(TEMPO_PAUSA)

        # RELATÓRIO FINAL
        log("\n" + "="*60)
        log("🏁 PROCESSAMENTO FINALIZADO!")
        log("="*60)
        log(f"✅ Sucessos: {sucessos}")
        log(f"❌ Erros: {erros}")
        log(f"⚠ Repetidos: {repetidos}")
        log(f"📊 Total processado: {total}")
        log(f"📄 Relatório completo: {RELATORIO}")
        log(f"📂 Prints salvos em: {PRINT_DIR}/")
        log("="*60)
        
    except KeyboardInterrupt:
        log("\n⚠ INTERROMPIDO PELO USUÁRIO")
        log(f"📊 Status até o momento:")
        log(f"   ✅ Sucessos: {sucessos}")
        log(f"   ❌ Erros: {erros}")
        
    except Exception as e:
        log(f"\n❌ ERRO FATAL: {e}")
        import traceback
        log(traceback.format_exc())
        
    finally:
        if driver:
            log("\n🔒 Mantendo navegador aberto para pagamento...")
            try:
                salvar_print(driver, "final")
                log("✔ Print final salvo")
                log("\n⚠ ATENÇÃO: O navegador permanecerá aberto!")
                log("🔑 Agora você pode fazer o login e efetuar o pagamento manualmente.")
                log("❌ Feche o navegador manualmente quando terminar.")
            except:
                log("⚠ Aguardando conclusão manual...")
        
        log(f"\n📄 Relatório final salvo em: {RELATORIO}")
        log(f"📋 Log completo salvo em: {LOG_FILE}")


if __name__ == "__main__":
    log("="*60)
    log("🎰 AUTOMAÇÃO MEGA-SENA - INICIANDO")
    log("="*60)
    principal()
    log("\n👋 Programa encerrado")