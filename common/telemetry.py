"""
All of your OpenTelemetry setup lives here.
"""

from opentelemetry import trace
from opentelemetry.instrumentation.starlette import StarletteInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


def configure_otel(enable_otel: bool) -> bool:
    """
    Initializes the global TracerProvider + exporters.
    Returns True if OTEL was configured, False if it should be skipped.
    """
    if not enable_otel:
        # skip exporting in debug, or still export to console?
        return False

    # set up resource and provider
    trace.set_tracer_provider(
        TracerProvider(resource=Resource.create({SERVICE_NAME: "thoas-local-dev"}))
    )
    provider = trace.get_tracer_provider()

    # use OTLP exporter
    otlp_exporter = OTLPSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # also log spans to console
    # console_processor = BatchSpanProcessor(ConsoleSpanExporter())
    # provider.add_span_processor(console_processor)

    return True


def instrument_app_if_enabled(app, enable_otel: bool) -> None:
    """
    Instruments the Starlette app if OTEL was configured.
    """
    if enable_otel:
        StarletteInstrumentor.instrument_app(app)
