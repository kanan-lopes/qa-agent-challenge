import os
import uuid

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
)


AWS_REGION = "us-east-1"

# Vamos colocar o ARN real depois de confirmar sua autenticação.
HARNESS_ARN = os.getenv("HARNESS_ARN")


def test_aws_identity():
    """
    Verifica se o boto3 consegue encontrar credenciais AWS válidas.
    Não exibe access key ou secret key.
    """
    print("\n[1] Verificando autenticação AWS...")

    sts = boto3.client("sts", region_name=AWS_REGION)

    identity = sts.get_caller_identity()

    print("✅ Autenticação AWS encontrada.")
    print(f"Conta: {identity['Account']}")
    print(f"Identidade: {identity['Arn']}")


def test_harness():
    """
    Executa uma única pergunta no Harness.
    """

    if not HARNESS_ARN:
        raise RuntimeError(
            "A variável de ambiente HARNESS_ARN ainda não foi configurada."
        )

    print("\n[2] Testando conexão com o AgentCore Harness...")

    client = boto3.client(
        "bedrock-agentcore",
        region_name=AWS_REGION,
    )

    session_id = str(uuid.uuid4())

    response = client.invoke_harness(
        harnessArn=HARNESS_ARN,
        qualifier="DEFAULT",
        runtimeSessionId=session_id,
        actorId="connection-test",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": (
                            "How many supplier quotations are required "
                            "for a R$ 6,000 purchase?"
                        )
                    }
                ],
            }
        ],
    )

    print("✅ Harness invocado.")
    print("\nResposta:\n")

    for event in response["stream"]:

        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})

            if "text" in delta:
                print(delta["text"], end="", flush=True)

        elif "runtimeClientError" in event:
            print(
                "\n❌ Erro retornado pelo runtime:",
                event["runtimeClientError"]["message"],
            )

    print()


def main():
    try:
        test_aws_identity()
        test_harness()

    except NoCredentialsError:
        print(
            "\n❌ O boto3 não encontrou credenciais AWS configuradas."
        )

    except PartialCredentialsError as error:
        print(
            "\n❌ As credenciais AWS estão incompletas:"
            f"\n{error}"
        )

    except ClientError as error:
        print("\n❌ Erro retornado pela AWS:")
        print(error)

    except BotoCoreError as error:
        print("\n❌ Erro do boto3:")
        print(error)

    except Exception as error:
        print("\n❌ Erro:")
        print(error)


if __name__ == "__main__":
    main()
