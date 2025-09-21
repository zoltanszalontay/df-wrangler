import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.w3c.trace_context_propagator import TraceContextPropagator

def setup_telemetry(app, service_name: str, otlp_endpoint: str):
    """
    Sets up OpenTelemetry for the FastAPI application.
    """
    resource = Resource.create(attributes={
        "service.name": service_name,
        "environment": os.getenv("ENVIRONMENT", "development")
    })

    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    set_global_textmap(TraceContextPropagator())

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Instrument requests library
    RequestsInstrumentor().instrument()

    # Instrument logging
    LoggingInstrumentor().instrument(set_logging_format=True)

    print(f"OpenTelemetry initialized for service: {service_name} with OTLP endpoint: {otlp_endpoint}")
